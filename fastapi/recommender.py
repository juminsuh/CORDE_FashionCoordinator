import faiss
import json
import numpy as np
import os

def load_metadata(db_path):
        with open(os.path.join(db_path, "metadata.jsonl"), "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

def load_faiss_index(db_path):
    index_path = os.path.join(db_path, "index.faiss")
    return faiss.read_index(index_path)

def retrieve(metadata, index, query_emb, category, negative, k=10):
    """
    이미 main category db만 필터링되어 들어오도록 함
    """
    query_emb = query_emb.reshape(1, -1).astype('float32')
    faiss.normalize_L2(query_emb)

    search_k = min(len(metadata), k * 20) 
    _, indices = index.search(query_emb, search_k)

    final_results = []
    for idx in indices[0]:
        if idx == -1: continue 
        
        item = metadata[idx]
        
        # hard filtering negatives
        if item.get("fit") in negative.get("fit", []): continue
        if item.get("pattern") in negative.get("pattern", []): continue
        if item.get("price") > negative.get("price", ""): continue
        
        final_results.append(item)
        
        if len(final_results) >= k:
            break
            
    return final_results
