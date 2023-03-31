#!/bin/bash
CLUSTERSYSTEM=""
LONGREADS_PATH=""
SHORTREADS_PATH=""
NBREADS_PER_JOB=""
NBJOBS=""
PENAME=""
QUEUE=""
NBTHREADS=4
LCORR_PATH=""
LBUILD_PATH=""
LORDEC_OUTPUT=""
NBMINUTES=120

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)

# LoRDEC binaries
LCORR_PATH=$DIR/lordec-correct
LBUILD_PATH=$DIR/lordec-build-SR-graph

printUsage() {
    echo "--slurm|--sge [-J nb_jobs | -N nb_reads_per_job] -P parallel_env_name -B lordec-build-SR-graph_PATH -C lordec-correct_PATH [-Q QUEUE_NAME] [-W NB_MINUTES_MAX] lordec_options..."
}

function join_by { local IFS="$1"; shift; echo "$*"; }

ARGS=$(getopt -o hT:i:2:N:J:P:B:C:o:k:s:t:b:e:S:ca:O:Q:W: -l "slurm,sge" -n "$0" -- "$@");

#Bad arguments
if [ $? -ne 0 ] || [ $# -eq 0 ];
then
    printUsage
    exit
fi
eval set -- "$ARGS";

while true; do
    case "$1" in
        --slurm)
            CLUSTERSYSTEM="slurm"
            shift;
            ;;
        --sge)
            CLUSTERSYSTEM="sge"
            shift;
            ;;
        -h)
            printUsage
            exit
            shift;
            ;;
        -2)
            shift;
            SHORTREADS_PATH=$1
            shift;
            ;;
        -i|--longread)
            shift;
            LONGREADS_PATH=$1
            shift;
            ;;
        -T|--nbthreads)
            shift;
            NBTHREADS=$1
            shift;
            ;;
        -J)
            shift;
            NBJOBS=$1
            shift;
            ;;
        -N)
            shift;
            NBREADS_PER_JOB=$1
            shift;
            ;;
        -P)
            shift;
            PENAME=$1
            shift;
            ;;
        -B)
            shift;
            LBUILD_PATH=$1
            shift;
            ;;
        -C)
            shift;
            LCORR_PATH=$1
            shift;
            ;;
        -o)
            shift;
            LORDEC_OUTPUT=$1
            shift;
            ;;
        -k)
            shift;
            K=$1
            shift;
            ;;
        -s)
            shift;
            S=$1
            shift;
            ;;
        -t)
            shift;
            EXTRAPARAMS="$EXTRAPARAMS -t $1"
            shift;
            ;;
        -b)
            shift;
            EXTRAPARAMS="$EXTRAPARAMS -b $1"
            shift;
            ;;
        -e)
            shift;
            EXTRAPARAMS="$EXTRAPARAMS -e $1"
            shift;
            ;;
        -S)
            shift;
            EXTRAPARAMS="$EXTRAPARAMS -S $1"
            shift;
            ;;
        -c)
            shift;
            EXTRAPARAMS="$EXTRAPARAMS -c"
            ;;
        -a)
            shift;
            EXTRAPARAMS="$EXTRAPARAMS -a $1"
            shift;
            ;;
        -O)
            shift;
            EXTRAPARAMS="$EXTRAPARAMS -O $1"
            shift;
            ;;
        -Q)
            shift;
            QUEUE="$1"
            shift;
            ;;
        -W)
            shift;
            NBMINUTES="$1"
            shift;
            ;;
        --)
            break;
            ;;
    esac
done

shift

# check that short reads, long read, lordec correct, lordec build graph exist
for p in "$LONGREADS_PATH" "$SHORTREADS_PATH" "$LCORR_PATH" "$LBUILD_PATH"; do
    if [ -z "$p" ] || [ ! -f "$p" ]; then
        echo "File \"$p\" not found."
        exit 1
    fi
done

if [ ! -x $LCORR_PATH ] || [ ! -x $LBUILD_PATH ]; then
    echo "LoRDEC binaries cannot be executed."
    exit 1
fi

for v in "$K" "$S"; do
    if [ -z $v ]; then
        echo "You must set -k and -s options"
        exit 1
    fi
done

# calculate NBREADS_PER_JOB if -J was set
if [ ! -z $NBJOBS ]; then
    nbreads=`grep -c "^>" $LONGREADS_PATH`
    ((NBREADS_PER_JOB=nbreads/NBJOBS+1))
fi

if [ -z $NBREADS_PER_JOB ]; then
    echo "You must set -J or -N option"
    exit 1
fi

if [ -z $CLUSTERSYSTEM ]; then
    echo "You must set --slurm or --sge to choose cluster system"
    exit 0
fi

if [[ $CLUSTERSYSTEM == "sge" ]]; then
    ############################# SGE ####################################
    if [ -z $PENAME ]; then
        echo "You must set a parallel environment name with -P option"
        exit 1
    fi
    if [ ! -z $QUEUE ]; then
        QUEUEARG="-q $QUEUE"
    fi
    TIMELIMITARG="-l h_rt=0:$NBMINUTES:0"

    SHORTREADS_NAME=`basename $SHORTREADS_PATH`

    # create result dir
    OUTPUT_DIR=`dirname $LORDEC_OUTPUT`
    RES_DIR=${OUTPUT_DIR}/lordec_`date +%Y-%m-%d_%H-%M-%S`
    RES_DIRNAME=`basename $RES_DIR`
    mkdir $RES_DIR

    ############ SPLIT ##########
    # job de découpage decoupage des long reads
    CMD="awk 'BEGIN {n_seq=0;ifile=0} /^>/ {if(n_seq%$NBREADS_PER_JOB==0){file=sprintf(\"$RES_DIR/myseq%03d.fa\",ifile); ifile++;} print >> file; n_seq++; next;} { print >> file; }' $LONGREADS_PATH"
    #awk 'BEGIN {n_seq=0;} /^>/ {if(n_seq%'$NBREADS_PER_JOB'==0){file=sprintf("'$RES_DIR'/myseq%d.fa",n_seq);} print >> file; n_seq++; next;} { print >> file; }' $LONGREADS_PATH
    # ne rend pas la main
    echo "cutting long read file in smaller pieces..."
    qsub $QUEUEARG $TIMELIMITARG -sync yes -e $RES_DIR/split_err.txt -o $RES_DIR/split_out.txt -cwd -N "split_${RES_DIRNAME}" -b y "$CMD" &
    pid_split=$!

    ############ GRAPH ##########
    # job de génération du graphe qui sera utilisé dans tous les jobs
    cp $SHORTREADS_PATH $RES_DIR/
    CMD="$LBUILD_PATH -2 $RES_DIR/$SHORTREADS_NAME -k $K -s $S -T $NBTHREADS -g $RES_DIR/${SHORTREADS_NAME}_k${K}_s${S}.h5"
    #./lordec-build-SR-graph -2 $SHORTREADS_NAME -k $K -s $S -g ./${SHORTREADS_NAME}_k${K}_s${S}.h5
    qsub $QUEUEARG $TIMELIMITARG -sync yes -pe $PENAME $NBTHREADS -e $RES_DIR/graph_err.txt -o $RES_DIR/graph_out.txt -cwd -N "graph_${RES_DIRNAME}" -b y "$CMD" &
    pid_graph=$!

    wait $pid_split
    ret_split=$?
    wait $pid_graph
    ret_graph=$?
    if ((ret_split != 0)); then
        echo "Failed to split input file ($ret_split)"
        exit 1
    fi
    if ((ret_graph != 0)); then
        echo "Failed to produce graph ($ret_graph)"
        exit 1
    fi

    ############ CORRECT ##########
    # lancement de N jobs à M coeurs, récup des JOBIDS
    i=1
    for f in $RES_DIR/myseq*.fa; do
        FNAME=`basename $f`
        CMD="$LCORR_PATH -T $NBTHREADS -i $f -2 $RES_DIR/$SHORTREADS_NAME -o $f.corrected.fa -k $K -s $S $EXTRAPARAMS"
        echo "#################################"
        echo $CMD
        echo "#################################"
        #./lordec-correct -T $NBTHREADS -k $K -s $S -i $f -2 $SHORTREADS_NAME -o $f.corrected.fa
        JOBNAME="correct_${RES_DIRNAME}_$FNAME"
        qsub $QUEUEARG $TIMELIMITARG -sync yes -e $RES_DIR/corr_${i}_err.txt -o $RES_DIR/corr_${i}_out.txt -cwd -N $JOBNAME -pe $PENAME $NBTHREADS -b y "$CMD" &
        pid=$!
        pidtab[$i]=$pid
        ((i++))
    done
    echo "Waiting for the LoRDEC jobs to finish"
    for n in ${!pidtab[@]}; do
        wait ${pidtab[${n}]}
        ret=$?
        if ((ret != 0)); then
            echo "LoRDEC job $n has failed ($ret)"
            exit 1
        fi
    done
    echo "All LoRDEC jobs finished successfully"

    ############ MERGE RESULTS ##########
    # job de concat des résultats qui dépend de tous les autres
    echo
    echo "Merging results..."
    CMD="cat $RES_DIR/*.corrected.fa > $RES_DIR/all_corrected.fa ; mv $RES_DIR/all_corrected.fa $LORDEC_OUTPUT ;"
    #cat $RES_DIR/*.corrected.fa > $RES_DIR/all_corrected.fa
    #echo $CMD
    qsub -sync yes $QUEUEARG $TIMELIMITARG -e $RES_DIR/merge_err.txt -o $RES_DIR/merge_out.txt -cwd -N "merge_${RES_DIRNAME}" -b y "$CMD"
    ret=$?
    if ((ret != 0)); then
        echo "LoRDEC merging failed ($ret)"
        exit 1
    fi
    echo "Merging LoRDEC results successfull. Deleting temp dir..."
    rm -rf $RES_DIR

    echo "Done"
    ############################# END SGE ####################################
else
    ############################# SLURM ####################################
    if [ ! -z $QUEUE ]; then
        QUEUEARG="--partition $QUEUE"
    fi
    TIMELIMITARG="--time=00:$NBMINUTES:00"

    SHORTREADS_NAME=`basename $SHORTREADS_PATH`

    # create result dir
    OUTPUT_DIR=`dirname $LORDEC_OUTPUT`
    RES_DIR=${OUTPUT_DIR}/lordec_`date +%Y-%m-%d_%H-%M-%S`
    RES_DIRNAME=`basename $RES_DIR`
    mkdir $RES_DIR

    ############ SPLIT ##########
    # job de découpage decoupage des long reads
    # ne rend pas la main
    echo "cutting long read file in smaller pieces..."
    srun -D ./ -e $RES_DIR/split_err.txt -o $RES_DIR/split_out.txt -N 1 -n 1 --ntasks-per-node 1 $QUEUEARG $TIMELIMITARG --job-name "split_${RES_DIRNAME}" awk 'BEGIN {n_seq=0;ifile=0} /^>/ {if(n_seq%'$NBREADS_PER_JOB'==0){file=sprintf("'$RES_DIR'/myseq%03d.fa",ifile); ifile++;} print >> file; n_seq++; next;} { print >> file; }' $LONGREADS_PATH
    pid_split=$!

    ############ GRAPH ##########
    # job de génération du graphe qui sera utilisé dans tous les jobs
    cp $SHORTREADS_PATH $RES_DIR/
    srun -D ./ -e $RES_DIR/graph_err.txt -o $RES_DIR/graph_out.txt -N 1 -n 1 --ntasks-per-node 1 $QUEUEARG $TIMELIMITARG --cpus-per-task $NBTHREADS --job-name "graph_${RES_DIRNAME}" $LBUILD_PATH -2 ${RES_DIR}/$SHORTREADS_NAME -k $K -s $S -T $NBTHREADS -g ${RES_DIR}/${SHORTREADS_NAME}_k${K}_s${S}.h5
    pid_graph=$!

    wait $pid_split
    ret_split=$?
    wait $pid_graph
    ret_graph=$?
    if ((ret_split != 0)); then
        echo "Failed to split input file ($ret_split)"
        exit 1
    fi
    if ((ret_graph != 0)); then
        echo "Failed to produce graph ($ret_graph)"
        exit 1
    fi

    ############ CORRECT ##########
    # lancement de N jobs à M coeurs, récup des JOBIDS
    i=1
    for f in $RES_DIR/myseq*.fa; do
        FNAME=`basename $f`
        CMD="$LCORR_PATH -T $NBTHREADS -i $f -2 $RES_DIR/$SHORTREADS_NAME -o $f.corrected.fa -k $K -s $S $EXTRAPARAMS"
        echo "#################################"
        echo $CMD
        echo "#################################"
        JOBNAME="correct_${RES_DIRNAME}_$FNAME"
        srun -D ./ -e $RES_DIR/corr_${i}_err.txt -o $RES_DIR/corr_${i}_out.txt -N 1 -n 1 --ntasks-per-node 1 $QUEUEARG $TIMELIMITARG --cpus-per-task $NBTHREADS --job-name "$JOBNAME" $LCORR_PATH -T $NBTHREADS -k $K -s $S -i $f -2 ${RES_DIR}/$SHORTREADS_NAME -o $f.corrected.fa $EXTRAPARAMS &
        pid=$!
        pidtab[$i]=$pid
        ((i++))
    done

    echo "Waiting the correction jobs to finish"
    for n in ${!pidtab[@]}; do
        wait ${pidtab[${n}]};
        ret=$?
        if ((ret != 0)); then
            echo "LoRDEC job $n has failed ($ret)"
            exit 1
        fi
    done
    echo "All LoRDEC jobs finished successfully"

    ############ MERGE RESULTS ##########
    echo
    echo "Merging results..."
    # job de concat des résultats qui dépend de tous les autres
    srun -D ./ -e $RES_DIR/merge_err.txt -o $RES_DIR/merge_out.txt -N 1 -n 1 --ntasks-per-node 1 $QUEUEARG $TIMELIMITARG --cpus-per-task 1 --job-name "merge_${RES_DIRNAME}" bash -c "cat $RES_DIR/*.corrected.fa > $RES_DIR/all_corrected.fa ; mv $RES_DIR/all_corrected.fa $LORDEC_OUTPUT"
    ret=$?
    if ((ret != 0)); then
        echo "LoRDEC merging failed ($ret)"
        exit 1
    fi
    echo "Merging LoRDEC results successfull. Deleting temp dir..."
    rm -rf $RES_DIR

    echo "Done"
fi
