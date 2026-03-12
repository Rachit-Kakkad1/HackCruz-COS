"""
train.py
─────────
Main entry point for fine-tuning FLAN-T5 Small on summarization.

Quick start:
    python train.py                                    # uses default config
    python train.py --config configs/train_config.yaml
    python train.py --config configs/train_config.yaml --custom_csv data/raw/my_data.csv
"""

import argparse
import logging
import os
import yaml

from src.data.dataset import load_hf_dataset, load_custom_dataset, tokenize_dataset
from src.model.model import load_model_and_tokenizer
from src.training.trainer import build_trainer

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune FLAN-T5 Small for summarization")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/train_config.yaml",
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--custom_csv",
        type=str,
        default=None,
        help="Path to a custom CSV dataset (overrides dataset_name in config)",
    )
    parser.add_argument(
        "--resume_from",
        type=str,
        default=None,
        help="Resume training from a checkpoint directory",
    )
    return parser.parse_args()


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    args = parse_args()
    cfg = load_config(args.config)

    logger.info("=" * 60)
    logger.info("  FLAN-T5 Small — Summarization Fine-Tuning")
    logger.info("=" * 60)
    logger.info(f"Config: {args.config}")

    # ── 1. Load model & tokenizer ──────────────────────────────────────────
    model, tokenizer = load_model_and_tokenizer(cfg["model"]["name"])

    # ── 2. Load dataset ────────────────────────────────────────────────────
    if args.custom_csv:
        logger.info(f"Using custom CSV dataset: {args.custom_csv}")
        raw_datasets = load_custom_dataset(
            csv_path=args.custom_csv,
            text_col=cfg["data"]["text_column"],
            summary_col=cfg["data"]["summary_column"],
            seed=cfg["training"]["seed"],
        )
    else:
        raw_datasets = load_hf_dataset(
            dataset_name=cfg["data"]["dataset_name"],
            dataset_config=cfg["data"].get("dataset_config"),
            num_train_samples=cfg["data"].get("num_train_samples"),
            num_val_samples=cfg["data"].get("num_val_samples"),
            seed=cfg["training"]["seed"],
        )

    # ── 3. Tokenize ────────────────────────────────────────────────────────
    tokenized_datasets = tokenize_dataset(
        dataset=raw_datasets,
        tokenizer=tokenizer,
        text_column=cfg["data"]["text_column"],
        summary_column=cfg["data"]["summary_column"],
        max_input_length=cfg["model"]["max_input_length"],
        max_target_length=cfg["model"]["max_target_length"],
    )

    # ── 4. Build trainer ───────────────────────────────────────────────────
    trainer = build_trainer(model, tokenizer, tokenized_datasets, cfg)

    # ── 5. Train ───────────────────────────────────────────────────────────
    logger.info("Starting training…")
    trainer.train(resume_from_checkpoint=args.resume_from)

    # ── 6. Save best model ─────────────────────────────────────────────────
    best_model_dir = os.path.join(cfg["training"]["output_dir"], "best")
    logger.info(f"Saving best model to: {best_model_dir}")
    trainer.save_model(best_model_dir)
    tokenizer.save_pretrained(best_model_dir)

    # ── 7. Final evaluation on validation set ──────────────────────────────
    logger.info("Running final evaluation…")
    results = trainer.evaluate()
    logger.info("Evaluation results:")
    for k, v in results.items():
        logger.info(f"  {k}: {v}")

    logger.info("=" * 60)
    logger.info("✅ Training complete!")
    logger.info(f"   Best model saved to: {best_model_dir}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
