import json
import sys
import numpy as np
import faiss
from pathlib import Path
from sklearn.preprocessing import normalize

# Insert project root to sys.path to allow importing from other directories
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

def load_latest_model(models_dir="models/embedding"):
    from sentence_transformers import SentenceTransformer
    base_model = "BAAI/bge-small-en-v1.5"
    m_dir = Path(models_dir)
    if not m_dir.exists():
        return SentenceTransformer(base_model)
    
    versions = []
    for d in m_dir.iterdir():
        if d.is_dir() and d.name.startswith("cos-embedding-v"):
            if (d / "READY").exists():
                try:
                    ver = int(d.name.replace("cos-embedding-v", ""))
                    versions.append((ver, d))
                except ValueError:
                    continue
    
    if not versions:
        return SentenceTransformer(base_model)
    
    latest_path = sorted(versions, key=lambda x: x[0])[-1][1]
    return SentenceTransformer(str(latest_path))

def mine_hard_negatives():
    data_path = Path("data/training_dataset.jsonl")
    if not data_path.exists():
        print(f"Error: {data_path} not found")
        return

    # Load triplets
    triplets = []
    with data_path.open("r", encoding="utf-8") as f:
        for line in f:
            triplets.append(json.loads(line))

    if not triplets:
        print("No triplets found in dataset.")
        return

    model = load_latest_model()
    
    # Extract unique anchors and their positive summaries for filtering
    anchor_info = {}
    for t in triplets:
        a = t['anchor']
        if a not in anchor_info:
            anchor_info[a] = {"positives": set()}
        anchor_info[a]["positives"].add(t['positive'])

    unique_anchors = list(anchor_info.keys())
    anchor_embeddings = model.encode(unique_anchors, show_progress_bar=False)
    anchor_embeddings = normalize(anchor_embeddings, norm='l2')

    # Build FAISS IndexFlatIP
    dim = anchor_embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(anchor_embeddings.astype("float32"))

    # Search top-20 nearest neighbors for each anchor
    D, I = index.search(anchor_embeddings.astype("float32"), 20)

    # Map anchor text to its index in unique_anchors
    anchor_to_idx = {text: i for i, text in enumerate(unique_anchors)}
    
    triplets_upgraded = 0
    triplets_kept = 0

    new_triplets = []
    for t in triplets:
        anchor_text = t['anchor']
        a_idx = anchor_to_idx[anchor_text]
        neighbor_indices = I[a_idx]
        
        positives = anchor_info[anchor_text]["positives"]
        
        hard_negative = None
        for n_idx in neighbor_indices:
            if n_idx < 0 or n_idx >= len(unique_anchors):
                continue
            neighbor_text = unique_anchors[n_idx]
            
            # Hard negative is the nearest neighbor that does NOT share the same positive text
            if neighbor_text != anchor_text and neighbor_text not in positives:
                hard_negative = neighbor_text
                break
        
        if hard_negative:
            t['negative'] = hard_negative
            triplets_upgraded += 1
        else:
            triplets_kept += 1
        new_triplets.append(t)

    # Overwrite dataset
    with data_path.open("w", encoding="utf-8") as f:
        for t in new_triplets:
            f.write(json.dumps(t) + "\n")

    print(f"triplets upgraded: {triplets_upgraded}")
    print(f"triplets kept as-is: {triplets_kept}")

if __name__ == "__main__":
    mine_hard_negatives()
