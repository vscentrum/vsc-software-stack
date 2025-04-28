use std::cmp::Reverse;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;

use futures::stream::FuturesUnordered;
use futures::StreamExt;
use polars_core::config;
use polars_core::frame::DataFrame;
use polars_core::prelude::{Column, PlHashSet, PlIndexMap, row_encode};
use polars_core::schema::SchemaRef;
use polars_core::utils::arrow::buffer::Buffer;
use polars_error::PolarsResult;
use polars_plan::dsl::{PartitionTargetCallback, SinkOptions};
use polars_utils::pl_str::PlSmallStr;
use polars_utils::priority::Priority;

use super::CreateNewSinkFn;
use crate::async_executor::{AbortOnDropHandle, spawn};
use crate::execute::StreamingExecutionState;
use crate::morsel::SourceToken;
use crate::nodes::io_sinks::partition::{SinkSender, open_new_sink};
use crate::nodes::io_sinks::phase::PhaseOutcome;
use crate::nodes::io_sinks::{SinkInputPort, SinkNode, parallelize_receive_task};
use crate::nodes::{JoinHandle, Morsel, MorselSeq, TaskPriority};

type Linearized = Priority<Reverse<MorselSeq>, (SourceToken, Vec<(Buffer<u8>, Vec<Column>, DataFrame)>)>;

pub struct PartitionByKeySinkNode {
    sink_input_schema: SchemaRef,
    key_cols: Arc<[PlSmallStr]>,
    max_open_partitions: usize,
    include_key: bool,
    base_path: Arc<PathBuf>,
    file_path_cb: Option<PartitionTargetCallback>,
    create_new: CreateNewSinkFn,
    ext: PlSmallStr,
    sink_options: SinkOptions,
}

impl PartitionByKeySinkNode {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        input_schema: SchemaRef,
        key_cols: Arc<[PlSmallStr]>,
        base_path: Arc<PathBuf>,
        file_path_cb: Option<PartitionTargetCallback>,
        create_new: CreateNewSinkFn,
        ext: PlSmallStr,
        sink_options: SinkOptions,
        include_key: bool,
    ) -> Self {
        assert!(!key_cols.is_empty());
        let mut sink_input_schema = input_schema.clone();
        if !include_key {
            let keys_col_hm = PlHashSet::from_iter(key_cols.iter().map(|s| s.as_str()));
            sink_input_schema = Arc::new(
                sink_input_schema
                    .try_project(
                        input_schema
                            .iter_names()
                            .filter(|n| !keys_col_hm.contains(n.as_str()))
                            .cloned(),
                    )
                    .unwrap(),
            );
        }
        const DEFAULT_MAX_OPEN_PARTITIONS: usize = 128;
        let max_open_partitions = std::env::var("POLARS_MAX_OPEN_PARTITIONS")
            .map_or(DEFAULT_MAX_OPEN_PARTITIONS, |v| {
                v.parse::<usize>().expect("unable to parse POLARS_MAX_OPEN_PARTITIONS")
            });

        Self {
            sink_input_schema,
            key_cols,
            max_open_partitions,
            include_key,
            base_path,
            file_path_cb,
            create_new,
            ext,
            sink_options,
        }
    }
}

impl SinkNode for PartitionByKeySinkNode {
    fn name(&self) -> &str {
        "partition-by-key"
    }

    fn is_sink_input_parallel(&self) -> bool {
        true
    }

    fn do_maintain_order(&self) -> bool {
        self.sink_options.maintain_order
    }

    fn spawn_sink(
        &mut self,
        recv_port_rx: crate::async_primitives::connector::Receiver<(PhaseOutcome, SinkInputPort)>,
        state: &StreamingExecutionState,
        join_handles: &mut Vec<JoinHandle<PolarsResult<()>>>,
    ) {
        let (pass_rxs, mut io_rx) = parallelize_receive_task::<Linearized>(
            join_handles,
            recv_port_rx,
            state.num_pipelines,
            self.sink_options.maintain_order,
        );

        join_handles.extend(pass_rxs.into_iter().map(|mut pass_rx| {
            let key_cols = self.key_cols.clone();
            let stable = self.sink_options.maintain_order;
            let include_key = self.include_key;
            spawn(TaskPriority::High, async move {
                while let Ok((mut rx, mut lin_tx)) = pass_rx.recv().await {
                    while let Ok(morsel) = rx.recv().await {
                        let (df, seq, source_token, consume_token) = morsel.into_inner();
                        let partitions = df._partition_by_impl(
                            &key_cols,
                            stable,
                            true,
                            false,
                        )?;

                        let partitions = partitions
                            .into_iter()
                            .map(|mut df| {
                                let keys = df.select_columns(key_cols.iter().cloned())?;
                                let keys = keys.into_iter().map(|c| c.head(Some(1))).collect::<Vec<_>>();
                                let row_encoded = row_encode::encode_rows_unordered(&keys)?
                                    .downcast_into_iter()
                                    .next()
                                    .unwrap()
                                    .into_inner()
                                    .2;
                                if !include_key {
                                    df = df.drop_many(key_cols.iter().cloned());
                                }
                                PolarsResult::Ok((row_encoded, keys, df))
                            })
                            .collect::<PolarsResult<Vec<_>>>()?;

                        if lin_tx.insert(Priority(Reverse(seq), (source_token, partitions))).await.is_err() {
                            return Ok(());
                        }
                        drop(consume_token);
                    }
                }
                Ok(())
            })
        }));

        let state = state.clone();
        let sink_input_schema = self.sink_input_schema.clone();
        let base_path = self.base_path.clone();
        let file_path_cb = self.file_path_cb.clone();
        let create_new_sink = self.create_new.clone();
        let ext = self.ext.clone();
        let max_open_partitions = self.max_open_partitions;
        let partitions_ref: Arc<Mutex<PlIndexMap<Buffer<u8>, OpenPartition>>> = Arc::new(Mutex::new(PlIndexMap::default()));

        join_handles.push(spawn(TaskPriority::High, {
            let partitions_ref = Arc::clone(&partitions_ref);
            async move {
                let verbose = config::verbose();
                let mut file_idx = 0;

                while let Ok(mut lin_rx) = io_rx.recv().await {
                    while let Some(Priority(Reverse(seq), (source_token, partitions))) = lin_rx.get().await {
                        for (row_encoded, keys, partition) in partitions {
                            let mut open_partitions = partitions_ref.lock().await;
                            let num_open = open_partitions.len();
                            match open_partitions.get_mut(&row_encoded) {
                                None if num_open >= max_open_partitions => {
                                    open_partitions.insert(row_encoded, OpenPartition::Buffer(keys, vec![partition]));
                                },
                                None => {
                                    let result = open_new_sink(
                                        base_path.as_path(),
                                        file_path_cb.as_ref(),
                                        super::default_by_key_file_path_cb,
                                        file_idx,
                                        file_idx,
                                        0,
                                        Some(keys.as_slice()),
                                        &create_new_sink,
                                        sink_input_schema.clone(),
                                        "by-key",
                                        ext.as_str(),
                                        verbose,
                                        &state,
                                    ).await?;
                                    file_idx += 1;
                                    let Some((join_handles, sender)) = result else { return Ok(()) };
                                    open_partitions.insert(row_encoded, OpenPartition::Sink(sender, join_handles));
                                },
                                Some(open_partition) => {
                                    match open_partition {
                                        OpenPartition::Sink(sender, _) => {
                                            let morsel = Morsel::new(partition, seq, source_token.clone());
                                            if sender.send(morsel).await.is_err() {
                                                return Ok(());
                                            }
                                        },
                                        OpenPartition::Buffer(_, buffer) => {
                                            buffer.push(partition);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                let open_partitions = Arc::try_unwrap(partitions_ref)
                    .map_err(|_| polars_error::PolarsError::ComputeError("Multiple Arc pointers detected".into()))?
                    .into_inner();

                for open_partition in open_partitions.into_values() {
                    match open_partition {
                        OpenPartition::Sink(sender, mut join_handles) => {
                            drop(sender);
                            while let Some(res) = join_handles.next().await {
                                res?;
                            }
                        },
                        OpenPartition::Buffer(keys, buffered) => {
                            let result = open_new_sink(
                                base_path.as_path(),
                                file_path_cb.as_ref(),
                                super::default_by_key_file_path_cb,
                                file_idx,
                                file_idx,
                                0,
                                Some(keys.as_slice()),
                                &create_new_sink,
                                sink_input_schema.clone(),
                                "by-key",
                                ext.as_str(),
                                verbose,
                                &state,
                            ).await?;
                            file_idx += 1;
                            let Some((mut join_handles, mut sender)) = result else { return Ok(()) };
                            let source_token = SourceToken::new();
                            let mut seq = MorselSeq::default();
                            for df in buffered {
                                let morsel = Morsel::new(df, seq, source_token.clone());
                                if sender.send(morsel).await.is_err() {
                                    return Ok(());
                                }
                                seq = seq.successor();
                            }
                            drop(sender);
                            while let Some(res) = join_handles.next().await {
                                res?;
                            }
                        }
                    }
                }

                Ok(())
            }
        }));
    }
}
enum OpenPartition {
    Sink(SinkSender, FuturesUnordered<AbortOnDropHandle<PolarsResult<()>>>),
    Buffer(Vec<Column>, Vec<DataFrame>),
}
