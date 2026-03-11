"""
COS Backend Lite — Clustering Engine.

Groups semantic snapshots into 'Tasks' using DBSCAN clustering.
Generates human-readable labels and categorizes tasks.
"""

import logging
import numpy as np
from sklearn.cluster import DBSCAN
from collections import Counter
import re

logger = logging.getLogger(__name__)

# Stopwords for simple heuristic labeling
STOPWORDS = {"the", "a", "an", "and", "or", "but", "if", "then", "else", "when", 
             "at", "by", "for", "with", "about", "against", "between", "into", 
             "through", "during", "before", "after", "above", "below", "to", 
             "from", "up", "down", "in", "out", "on", "off", "over", "under", 
             "again", "further", "then", "once", "here", "there", "when", 
             "where", "why", "how", "all", "any", "both", "each", "few", 
             "more", "most", "other", "some", "such", "no", "nor", "not", 
             "only", "own", "same", "so", "than", "too", "very", "s", "t", 
             "can", "will", "just", "don", "should", "now", "i", "my", "me"}

def cluster_contexts(contexts: list[dict], embeddings: np.ndarray):
    """
    Groups raw contexts into semantic tasks using DBSCAN.
    
    Args:
        contexts: List of context metadata from SQLite.
        embeddings: (N, 384) array of embeddings from FAISS.
        
    Returns:
        nodes: List of task-level nodes for the graph.
        edges: List of edges between tasks.
    """
    if not contexts:
        return [], []

    # 1. Run DBSCAN
    # eps is the distance threshold (1 - similarity). 0.25 eps ~ 0.75 similarity.
    # min_samples=1 so every node belongs to at least one cluster.
    clustering = DBSCAN(eps=0.3, min_samples=1, metric='cosine').fit(embeddings)
    labels = clustering.labels_

    # 2. Group contexts by cluster label
    clusters = {}
    for idx, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(contexts[idx])

    # 3. Process each cluster into a "Task" node
    task_nodes = []
    for label, group in clusters.items():
        # Heuristic: Create a task label from the most common words in titles
        all_titles = " ".join([c['title'] for c in group])
        # Remove common technical noise
        cleaned_titles = re.sub(r'https?://\S+|localhost:\d+|v\d+', '', all_titles)
        words = re.findall(r'\w+', cleaned_titles.lower())
        filtered_words = [w for w in words if w not in STOPWORDS and len(w) > 2]
        
        # Get top words, but prioritize nouns/verbs by length
        top_words = [w[0] for w in Counter(filtered_words).most_common(5)]
        task_label = " ".join(top_words[:2]).title() or group[0]['title']
        
        # Advanced Categorization
        text_blob = (all_titles + " " + " ".join([c.get('summary', '') for c in group])).lower()
        
        if any(w in text_blob for w in ["code", "py", "js", "html", "css", "git", "vscode", "npm", "rust", "react"]):
            category = "Coding"
        elif any(w in text_blob for w in ["write", "doc", "notion", "edit", "proposal", "slack", "mail", "chat"]):
            category = "Writing"
        elif any(w in text_blob for w in ["research", "wiki", "paper", "learn", "study", "analysis"]):
            category = "Research"
        elif any(w in text_blob for w in ["google", "browse", "amazon", "youtube", "twitter", "reddit"]):
            category = "Browsing"
        else:
            category = "Activity"

        # Representative metadata
        latest = sorted(group, key=lambda x: x['timestamp'], reverse=True)[0]
        
        task_nodes.append({
            "id": f"task_{label}",
            "label": task_label if len(task_label) > 3 else "Active Context",
            "category": category,
            "summary": f"Semantic cluster of {len(group)} context events detected.",
            "count": len(group),
            "last_active": latest['timestamp'],
            "contexts": group,
            "url": latest['url']
        })

    # 4. Generate edges between tasks (optional, based on inter-cluster similarity)
    # For now, let's just return the tasks. Edges are harder with clusters.
    # A simple approach: if two tasks share raw context edges, they are linked.
    # But for a "Future OS" feel, maybe just show the distinct tasks for now.
    
    return task_nodes, []
