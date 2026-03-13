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
        # Representative metadata
        latest = sorted(group, key=lambda x: x['timestamp'], reverse=True)[0]
        
        # Heuristic: Create a task label from the most common words or best title
        # For small clusters, use the latest title as basis
        if len(group) <= 2:
            task_label = latest['title']
        else:
            all_titles = " ".join([c['title'] for c in group])
            cleaned_titles = re.sub(r'https?://\S+|localhost:\d+|v\d+|-|_', ' ', all_titles)
            words = re.findall(r'\w+', cleaned_titles.lower())
            filtered_words = [w for w in words if w not in STOPWORDS and len(w) > 3]
            
            # Use top words to construct a label
            freq = Counter(filtered_words).most_common(3)
            if freq:
                task_label = " ".join([w[0] for w in freq]).title()
            else:
                task_label = latest['title']

        # Categorization logic
        text_blob = (all_titles + " " + " ".join([c.get('summary', '') or '' for c in group])).lower()
        if any(w in text_blob for w in ["code", "py", "js", "ts", "html", "css", "git", "vscode", "npm", "rust", "react", "terminal"]):
            category = "Coding"
        elif any(w in text_blob for w in ["write", "doc", "notion", "edit", "proposal", "slack", "mail", "chat", "discord"]):
            category = "Writing"
        elif any(w in text_blob for w in ["research", "wiki", "paper", "learn", "study", "analysis", "arxiv"]):
            category = "Research"
        elif any(w in text_blob for w in ["google", "browse", "amazon", "youtube", "twitter", "reddit", "facebook"]):
            category = "Browsing"
        else:
            category = "Activity"

        # Limit label length
        if len(task_label) > 40:
            task_label = task_label[:37] + "..."

        task_nodes.append({
            "id": f"task_{label}",
            "label": task_label,
            "category": category,
            "summary": f"Task involving {len(group)} interactions. Priority: {category}.",
            "count": len(group),
            "last_active": latest['timestamp'],
            "timestamp": latest['timestamp'], # For frontend compatibility
            "contexts": group,
            "app": latest.get('app', category),
            "url": latest['url']
        })

    # 4. Generate edges between tasks based on overlap or similarity
    # Simple approach: If any context in task A is similar to any in task B
    # But for performance in windowed mode, we can just return nodes for now.
    return task_nodes, []
