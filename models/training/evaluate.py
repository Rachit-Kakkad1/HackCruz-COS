"""
evaluate.py
────────────
Run ROUGE evaluation on the test set using a fine-tuned model.

Usage:
    python evaluate.py --model_path outputs/checkpoints/best
    python evaluate.py --model_path outputs/checkpoints/best --num_samples 500
"""

import argparse
import logging
import yaml

from src.data.dataset import load_hf_dataset, tokenize_dataset
from src.model.model import load_model_and_tokenizer
from src.training.trainer import build_trainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True, help="Path to fine-tuned model")
    parser.add_argument("--config", type=str, default="configs/train_config.yaml")
    parser.add_argument("--num_samples", type=int, default=None, help="Limit test samples")
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    logger.info(f"Loading model from: {args.model_path}")
    model, tokenizer = load_model_and_tokenizer(args.model_path)

    # Load test split
    logger.info("Loading test dataset…")
    dataset = load_hf_dataset(
        dataset_name=cfg["data"]["dataset_name"],
        dataset_config=cfg["data"].get("dataset_config"),
        seed=cfg["training"]["seed"],
    )

    if args.num_samples:
        dataset["test"] = dataset["test"].select(range(args.num_samples))

    # Use test split as val for evaluation
    dataset["validation"] = dataset["test"]

    tokenized = tokenize_dataset(
        dataset=dataset,
        tokenizer=tokenizer,
        text_column=cfg["data"]["text_column"],
        summary_column=cfg["data"]["summary_column"],
        max_input_length=cfg["model"]["max_input_length"],
        max_target_length=cfg["model"]["max_target_length"],
    )

    trainer = build_trainer(model, tokenizer, tokenized, cfg)

    logger.info("Running evaluation on test set…")
    results = trainer.evaluate(eval_dataset=tokenized["validation"])

    print("\n" + "=" * 50)
    print("📊 TEST SET EVALUATION RESULTS")
    print("=" * 50)
    for k, v in results.items():
        print(f"  {k:30s}: {v:.4f}" if isinstance(v, float) else f"  {k:30s}: {v}")
    print("=" * 50)


if __name__ == "__main__":
    main()
