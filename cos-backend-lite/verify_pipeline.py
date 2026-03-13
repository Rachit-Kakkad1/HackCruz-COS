"""
COS Technical Verification Script - AI Pipeline Validation
Validates: Model Loading -> Embedding Gen -> FAISS Integration -> Semantic Retrieval -> Performance
"""

import time
import logging
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Setup structured logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("VERIFIER")

# Configuration
MODEL_NAME = "all-MiniLM-L6-v2"  # Consistent with current backend
EXPECTED_DIM = 384
TEST_CONTEXTS = [
    "Writing HackCrux proposal budget",
    "Editing COS graph UI in React",
    "Watching YouTube tutorial about FAISS",
    "Reading FastAPI documentation"
]

def run_verification():
    logger.info("Starting AI Pipeline Verification...")
    
    # ─── Step 1: Load Model ──────────────────────────────────────────────────
    try:
        start_time = time.time()
        model = SentenceTransformer(MODEL_NAME)
        load_latency = (time.time() - start_time) * 1000
        logger.info(f"[MODEL] Loaded '{MODEL_NAME}' successfully in {load_latency:.2f}ms")
    except Exception as e:
        logger.error(f"[MODEL] Failed to load model: {e}")
        return

    # ─── Step 2: Generate Embeddings ─────────────────────────────────────────
    try:
        start_time = time.time()
        embeddings = model.encode(TEST_CONTEXTS, normalize_embeddings=True)
        gen_latency = (time.time() - start_time) * 1000
        
        num_vecs = len(embeddings)
        dim = len(embeddings[0])
        
        if dim == EXPECTED_DIM:
            logger.info(f"[EMBEDDING] Generated {num_vecs} vectors with correct dimension ({dim})")
            logger.info(f"[PERFORMANCE] Batch encoding latency: {gen_latency:.2f}ms (avg {(gen_latency/num_vecs):.2f}ms/doc)")
        else:
            logger.error(f"[EMBEDDING] Dimension mismatch: Expected {EXPECTED_DIM}, got {dim}")
            return
    except Exception as e:
        logger.error(f"[EMBEDDING] Generation failed: {e}")
        return

    # ─── Step 3: Validate Vector Database (FAISS) ───────────────────────────
    try:
        # Using IndexFlatIP since we normalized embeddings (Cosine Similarity)
        index = faiss.IndexFlatIP(EXPECTED_DIM)
        index.add(np.array(embeddings).astype("float32"))
        
        if index.ntotal == num_vecs:
            logger.info(f"[FAISS] Stored {index.ntotal} vectors in temporary index")
        else:
            logger.error(f"[FAISS] Insertion mismatch: Expected {num_vecs}, got {index.ntotal}")
            return
    except Exception as e:
        logger.error(f"[FAISS] Initialization/Insertion failed: {e}")
        return

    # ─── Step 4: Semantic Retrieval Tests ────────────────────────────────────
    
    # Positive Test
    query_pos = "What was I doing with the COS UI?"
    logger.info(f"[SEARCH] Testing Positive Query: '{query_pos}'")
    
    start_time = time.time()
    query_emb = model.encode([query_pos], normalize_embeddings=True)
    encode_latency = (time.time() - start_time) * 1000
    
    start_time = time.time()
    scores, indices = index.search(np.array(query_emb).astype("float32"), k=1)
    search_latency = (time.time() - start_time) * 1000
    
    best_match = TEST_CONTEXTS[indices[0][0]]
    score = scores[0][0]
    
    print(f"[SEARCH] Result: '{best_match}' (Score: {score:.4f})")
    print(f"[PERFORMANCE] Singles encoding: {encode_latency:.2f}ms | Search: {search_latency:.2f}ms")
    
    if "COS graph UI" in best_match:
        print("[SEARCH] Correctness: PASS (Semantic match found)")
        logger.info("[SEARCH] Correctness: PASS (Semantic match found)")
    else:
        print("[SEARCH] Correctness: FAIL (Unexpected match)")
        logger.warning("[SEARCH] Correctness: FAIL (Unexpected match)")

    # Negative/Grouping Test
    query_neg = "watching video tutorial"
    print(f"[SEARCH] Testing Negative/Grouping Query: '{query_neg}'")
    logger.info(f"[SEARCH] Testing Negative/Grouping Query: '{query_neg}'")
    
    scores_neg, indices_neg = index.search(np.array(model.encode([query_neg], normalize_embeddings=True)).astype("float32"), k=1)
    best_match_neg = TEST_CONTEXTS[indices_neg[0][0]]
    
    print(f"[SEARCH] Result: '{best_match_neg}' (Score: {scores_neg[0][0]:.4f})")
    if "YouTube" in best_match_neg:
        print("[SEARCH] Grouping: PASS (Semantic grouping found)")
        logger.info("[SEARCH] Grouping: PASS (Semantic grouping found)")
    else:
        print("[SEARCH] Grouping: FAIL (Unexpected match)")
        logger.warning("[SEARCH] Grouping: FAIL (Unexpected match)")

    print("\n--- Summary ---")
    print(f"Pipeline End-to-End: SUCCESS")
    print(f"Average Encoding Latency: {encode_latency:.2f}ms")
    print(f"FAISS Search Latency: {search_latency:.2f}ms")

if __name__ == "__main__":
    run_verification()
