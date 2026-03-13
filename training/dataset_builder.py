import sqlite3
import json
import random
import argparse
from pathlib import Path

def build_dataset(db_path: Path, output_path: Path):
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query contexts with summary and cluster_id
        cursor.execute("""
            SELECT id, summary, cluster_id 
            FROM contexts 
            WHERE summary IS NOT NULL AND cluster_id IS NOT NULL
        """)
        rows = cursor.fetchall()

    cluster_map = {}
    for row in rows:
        cid = row['cluster_id']
        if cid not in cluster_map:
            cluster_map[cid] = []
        cluster_map[cid].append({"id": row['id'], "summary": row['summary']})

    triplets = []
    all_cluster_ids = list(cluster_map.keys())
    
    contexts_processed = 0
    for cid, members in cluster_map.items():
        if len(members) < 3:  # need anchor + 2 others
            continue
            
        other_clusters = [ocid for ocid in all_cluster_ids if ocid != cid]
        # Need at least 2 other clusters to safely sample negatives if we want 2 negatives per context
        # But requirement says 2 negatives available. 
        # Actually total negatives available across all other clusters.
        available_negatives = []
        for ocid in other_clusters:
            available_negatives.extend(cluster_map[ocid])
            
        if len(available_negatives) < 2:
            continue

        for anchor in members:
            contexts_processed += 1
            positives = [m for m in members if m['id'] != anchor['id']]
            
            # Use random.sample to avoid duplicates
            # Requirement: at least 2 positives and 2 negatives available
            if len(positives) < 2:
                continue
                
            sampled_positives = random.sample(positives, 2)
            sampled_negatives = random.sample(available_negatives, 2)
            
            for pos in sampled_positives:
                for neg in sampled_negatives:
                    triplets.append({
                        "anchor": anchor['summary'],
                        "positive": pos['summary'],
                        "negative": neg['summary']
                    })

    with output_path.open("w", encoding="utf-8") as f:
        for t in triplets:
            f.write(json.dumps(t) + "\n")

    print(f"Total contexts processed: {contexts_processed}")
    print(f"Total triplets written: {len(triplets)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", type=str, nargs="?", default="../cos.db")
    args = parser.parse_args()
    
    db_p = Path(args.db_path).resolve()
    out_p = Path("data/training_dataset.jsonl").resolve()
    
    build_dataset(db_p, out_p)
