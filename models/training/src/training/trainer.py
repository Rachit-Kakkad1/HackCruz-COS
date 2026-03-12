"""
src/training/trainer.py
────────────────────────
Builds TrainingArguments and Seq2SeqTrainer from config.
"""

import logging
from typing import Dict, Any

from transformers import (
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
    PreTrainedTokenizer,
    T5ForConditionalGeneration,
)
from datasets import DatasetDict

from src.training.metrics import build_compute_metrics

logger = logging.getLogger(__name__)


def build_training_args(cfg: Dict[str, Any]) -> Seq2SeqTrainingArguments:
    """Construct Seq2SeqTrainingArguments from the YAML config dict."""
    t = cfg["training"]
    g = cfg["generation"]
    log = cfg["logging"]

    return Seq2SeqTrainingArguments(
        output_dir=t["output_dir"],
        num_train_epochs=t["num_epochs"],
        per_device_train_batch_size=t["train_batch_size"],
        per_device_eval_batch_size=t["eval_batch_size"],
        learning_rate=t["learning_rate"],
        weight_decay=t["weight_decay"],
        warmup_steps=t["warmup_steps"],
        gradient_accumulation_steps=t["gradient_accumulation_steps"],
        fp16=t["fp16"],
        bf16=t["bf16"],
        eval_strategy="steps",
        eval_steps=t["eval_steps"],
        save_strategy="steps",
        save_steps=t["save_steps"],
        logging_steps=t["logging_steps"],
        save_total_limit=t["save_total_limit"],
        load_best_model_at_end=t["load_best_model_at_end"],
        metric_for_best_model=t["metric_for_best_model"],
        greater_is_better=t["greater_is_better"],
        predict_with_generate=True,               # ← essential for Seq2Seq
        generation_num_beams=g["num_beams"],
        seed=t["seed"],
        report_to=log["report_to"],
        logging_dir=log["log_dir"],
        run_name=log["run_name"],
    )


def build_trainer(
    model: T5ForConditionalGeneration,
    tokenizer: PreTrainedTokenizer,
    tokenized_datasets: DatasetDict,
    cfg: Dict[str, Any],
) -> Seq2SeqTrainer:
    """Assemble and return the Seq2SeqTrainer."""

    training_args = build_training_args(cfg)

    # Dynamic padding collator (pads each batch to its longest example)
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        label_pad_token_id=-100,
        pad_to_multiple_of=8 if (training_args.fp16 or training_args.bf16) else None,
    )

    compute_metrics = build_compute_metrics(tokenizer)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets.get("validation"),
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    logger.info("Trainer built successfully.")
    return trainer
