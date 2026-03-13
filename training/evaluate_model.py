import json
import random
import argparse
import sys
import torch
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_accuracy(model_path: str, eval_triplets: list):
    model = SentenceTransformer(model_path)
    
    anchors = [t['anchor'] for t in eval_triplets]
    positives = [t['positive'] for t in eval_triplets]
    
    anchor_embeddings = model.encode(anchors, show_progress_bar=False)
    positive_embeddings = model.encode(positives, show_progress_bar=False)
    
    # Compute similarity matrix (len(anchors), len(positives))
    sim_matrix = cosine_similarity(anchor_embeddings, positive_embeddings)
    
    hits = 0
    for i in range(len(anchors)):
        # Check if the correct positive (at index i) is the rank-1 result
        if np.argmax(sim_matrix[i]) == i:
            hits += 1
            
    return hits / len(anchors)

def evaluate(new_model_path: str, old_model_path: str):
    eval_path = Path("data/eval_set.jsonl")
    dataset_path = Path("data/training_dataset.jsonl")
    
    if not eval_path.exists():
        if not dataset_path.exists():
            print("Error: training_dataset.jsonl not found to create eval set.")
            return
            
        triplets = []
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                triplets.append(json.loads(line))
        
        if not triplets:
            print("Error: training_dataset.jsonl is empty.")
            return

        sample_size = min(200, len(triplets))
        eval_triplets = random.sample(triplets, sample_size)
        
        eval_path.parent.mkdir(parents=True, exist_ok=True)
        with eval_path.open("w", encoding="utf-8") as f:
            for t in eval_triplets:
                f.write(json.dumps(t) + "\n")
        
        print("Eval set created — re-run to evaluate.")
        sys.exit(2)

    # Load eval set
    eval_triplets = []
    with eval_path.open("r", encoding="utf-8") as f:
        for line in f:
            eval_triplets.append(json.loads(line))

    print(f"Evaluating {new_model_path} vs {old_model_path} on {len(eval_triplets)} samples...")
    
    new_acc = calculate_accuracy(new_model_path, eval_triplets)
    
    # Memory management before loading second model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    old_acc = calculate_accuracy(old_model_path, eval_triplets)
    
    print(f"New model accuracy: {new_acc:.4f}")
    print(f"Old model accuracy: {old_acc:.4f}")
    
    if new_acc > old_acc:
        print("DEPLOY")
        sys.exit(0)
    else:
        print("KEEP_CURRENT")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-model", type=str, required=True)
    parser.add_argument("--old-model", type=str, required=True)
    args = parser.parse_args()
    
    evaluate(args.new_model, args.old_model)
