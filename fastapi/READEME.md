```
fastapi/
├── main.py 
├── persona.py # persona summary 
├── recommender.py # tools for search items
├── utils.py 
├── db/
│   ├── metadata.jsonl # metadata of item
│   └── top
│    │    └── index.faiss # item embeddings
│    │    └── metadata.jsonl
│    └── bottom
│        └── index.faiss # item embeddings
│         └── metadata.jsonl
│         ...
│
├── requirements.txt # install
```