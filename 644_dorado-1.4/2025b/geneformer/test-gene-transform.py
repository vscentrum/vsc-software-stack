#!/usr/bin/env python3
import argparse
import math
import pickle
import tempfile
from pathlib import Path

import torch
import transformers
from datasets import Dataset
from packaging.version import Version
from transformers import BertConfig, BertForMaskedLM, TrainingArguments

from geneformer import TOKEN_DICTIONARY_FILE
from geneformer.pretrainer import GeneformerPretrainer


def ok(msg):
    print(f"[OK] {msg}")


def fail(msg):
    raise RuntimeError(msg)


def load_token_dictionary():
    with open(TOKEN_DICTIONARY_FILE, "rb") as fh:
        token_dict = pickle.load(fh)
    missing = [token for token in ["<pad>", "<mask>"] if token not in token_dict]
    if missing:
        fail(f"Geneformer token dictionary is missing special tokens: {missing}")
    gene_ids = [
        value for key, value in token_dict.items()
        if isinstance(value, int) and not str(key).startswith("<")
    ]
    if len(gene_ids) < 64:
        fail("Geneformer token dictionary contains too few ordinary gene tokens")
    ok(f"Geneformer token dictionary loaded ({len(token_dict)} tokens)")
    return token_dict, gene_ids


def make_dataset(gene_ids):
    lengths = [12, 19, 14, 18, 13, 17, 15, 16]
    rows = []
    offset = 0
    for length in lengths:
        ids = gene_ids[offset:offset + length]
        if len(ids) != length:
            fail("Not enough token IDs to construct synthetic dataset")
        rows.append({"input_ids": ids, "length": length})
        offset += length
    return Dataset.from_list(rows), lengths


def make_model(token_dict):
    vocab_size = max(token_dict.values()) + 1
    config = BertConfig(
        vocab_size=vocab_size,
        hidden_size=32,
        num_hidden_layers=1,
        num_attention_heads=4,
        intermediate_size=64,
        max_position_embeddings=128,
        pad_token_id=token_dict["<pad>"],
    )
    model = BertForMaskedLM(config)
    ok(f"Tiny BertForMaskedLM created (vocab_size={vocab_size})")
    return model


def main():
    parser = argparse.ArgumentParser(
        description="Test Geneformer GeneformerPretrainer compatibility with Transformers."
    )
    parser.add_argument("--expected-transformers", default="4.57.1")
    parser.add_argument("--require-cuda", action="store_true")
    args = parser.parse_args()

    print("=== Geneformer / Transformers compatibility test ===")
    print(f"[INFO] Transformers {transformers.__version__}")
    print(f"[INFO] PyTorch {torch.__version__}")
    print(f"[INFO] CUDA build: {torch.version.cuda}")
    print(f"[INFO] CUDA available: {torch.cuda.is_available()}")

    if Version(transformers.__version__) != Version(args.expected_transformers):
        fail(
            f"Expected Transformers {args.expected_transformers}, "
            f"found {transformers.__version__}"
        )
    if args.require_cuda and not torch.cuda.is_available():
        fail("--require-cuda was requested but torch.cuda.is_available() is False")
    ok(f"Expected Transformers version {args.expected_transformers} is loaded")

    token_dict, gene_ids = load_token_dictionary()
    dataset, lengths = make_dataset(gene_ids)
    ok(f"Synthetic Hugging Face Dataset created ({len(dataset)} examples)")

    with tempfile.TemporaryDirectory(prefix="geneformer-transformers-") as tmp:
        tmp = Path(tmp)
        lengths_file = tmp / "lengths.pkl"
        with open(lengths_file, "wb") as fh:
            pickle.dump(lengths, fh)

        training_args = TrainingArguments(
            output_dir=str(tmp / "output"),
            overwrite_output_dir=True,
            per_device_train_batch_size=2,
            max_steps=1,
            learning_rate=5e-4,
            group_by_length=True,
            save_strategy="no",
            logging_strategy="no",
            report_to=[],
            disable_tqdm=True,
            dataloader_num_workers=0,
            remove_unused_columns=True,
            optim="adamw_torch",
            use_cpu=not torch.cuda.is_available(),
            seed=1234,
        )

        model = make_model(token_dict)
        trainer = GeneformerPretrainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            token_dictionary=token_dict,
            example_lengths_file=str(lengths_file),
            mlm=True,
            mlm_probability=1.0,
        )
        ok("GeneformerPretrainer instantiated with Transformers Trainer")

        sampler = trainer._get_train_sampler()
        if sampler is None:
            fail("GeneformerPretrainer._get_train_sampler() returned None")
        if "LengthGroupedSampler" not in type(sampler).__name__:
            fail(f"Unexpected sampler type: {type(sampler).__name__}")
        ok(f"Geneformer group-by-length sampler works ({type(sampler).__name__})")

        dataloader = trainer.get_train_dataloader()
        batch = next(iter(dataloader))
        missing = {"input_ids", "labels"}.difference(batch)
        if missing:
            fail(f"Geneformer MLM collator batch is missing fields: {sorted(missing)}")
        if batch["input_ids"].shape != batch["labels"].shape:
            fail(
                f"input_ids shape {tuple(batch['input_ids'].shape)} does not match "
                f"labels shape {tuple(batch['labels'].shape)}"
            )
        if not torch.any(batch["labels"] != -100):
            fail("MLM collator produced no supervised tokens")
        ok(
            "Geneformer DataCollatorForLanguageModeling works "
            f"(batch shape={tuple(batch['input_ids'].shape)})"
        )

        result = trainer.train()
        if trainer.state.global_step != 1:
            fail(f"Expected one training step, got {trainer.state.global_step}")
        if not math.isfinite(result.training_loss):
            fail(f"Training loss is not finite: {result.training_loss}")

        device = trainer.args.device
        if args.require_cuda and device.type != "cuda":
            fail(f"Trainer did not select CUDA; selected device is {device}")
        ok(f"GeneformerPretrainer completed one real training step on {device}")
        ok(f"Training loss is finite: {result.training_loss:.6f}")

    print("=== PASS: Geneformer is compatible with this Transformers Trainer path ===")


if __name__ == "__main__":
    main()
