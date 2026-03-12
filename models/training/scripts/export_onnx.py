"""
scripts/export_onnx.py
───────────────────────
Export the encoder of a fine-tuned FLAN-T5 model to ONNX
for fast CPU inference in production.

Usage:
    python scripts/export_onnx.py --model_path outputs/checkpoints/best
    python scripts/export_onnx.py --model_path outputs/checkpoints/best --output_path outputs/exports/encoder.onnx
"""

import argparse
import logging
import os

import torch
from transformers import AutoTokenizer, T5ForConditionalGeneration

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def export_encoder_to_onnx(model_path: str, output_path: str, max_length: int = 512):
    """Export encoder to ONNX format."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info(f"Loading model: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
    model = T5ForConditionalGeneration.from_pretrained(model_path)
    encoder = model.encoder
    encoder.eval()

    # Dummy input for tracing
    dummy_text = "summarize: This is a sample input text for ONNX export tracing."
    inputs = tokenizer(
        dummy_text,
        return_tensors="pt",
        max_length=max_length,
        truncation=True,
        padding="max_length",
    )

    logger.info(f"Exporting encoder to ONNX: {output_path}")
    with torch.no_grad():
        torch.onnx.export(
            encoder,
            (inputs["input_ids"], inputs["attention_mask"]),
            output_path,
            opset_version=14,
            input_names=["input_ids", "attention_mask"],
            output_names=["last_hidden_state"],
            dynamic_axes={
                "input_ids": {0: "batch_size", 1: "sequence_length"},
                "attention_mask": {0: "batch_size", 1: "sequence_length"},
                "last_hidden_state": {0: "batch_size", 1: "sequence_length"},
            },
            do_constant_folding=True,
        )

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"✅ Export complete! File size: {size_mb:.1f} MB → {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Export FLAN-T5 encoder to ONNX")
    parser.add_argument("--model_path", type=str, required=True, help="Fine-tuned model directory")
    parser.add_argument(
        "--output_path",
        type=str,
        default="outputs/exports/encoder.onnx",
        help="Output ONNX file path",
    )
    parser.add_argument("--max_length", type=int, default=512)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    export_encoder_to_onnx(args.model_path, args.output_path, args.max_length)
