from fastapi import FastAPI
from pydantic import BaseModel
import time

from persona import PERSONA_MAP
from recommender import load_metadata, load_faiss_index, retrieve
from utils import parse_tpo, clip_embed, generate_reason

app = FastAPI(title="Fashion Demo API")

CATEGORY_ORDER = ["상의", "하의", "아우터", "가방", "신발"]
SESSIONS = {}

# ---------- Session Utils ----------

def get_session(session_id: str):
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            "persona": None,
            "negative": {},
            "parsed_tpo": [],
            "selected_items": [],
            "current_step": CATEGORY_ORDER[0],
            "created_at": time.time()
        }
    return SESSIONS[session_id]

# ---------- Request Models ----------

class PersonaReq(BaseModel):
    session_id: str
    persona_key: str

class NegativeReq(BaseModel):
    session_id: str
    fit: list[str]
    pattern: list[str]
    price_threshold: list[str]

class TPOReq(BaseModel):
    session_id: str
    tpo_text: str

class SelectReq(BaseModel):
    session_id: str
    item_id: str

# ---------- APIs ----------

@app.post("/step/persona")
def select_persona(req: PersonaReq):
    state = get_session(req.session_id)
    state["persona"] = PERSONA_MAP[req.persona_key]
    return {"message": "persona saved"}

@app.post("/step/negative")
def save_negative(req: NegativeReq):
    state = get_session(req.session_id)
    state["negative"] = {
        "fit": req.fit,
        "pattern": req.pattern,
        "price": req.price
    }
    return {"message": "negative saved"}

@app.post("/step/tpo")
def save_tpo(req: TPOReq):
    state = get_session(req.session_id)
    state["parsed_tpo"] = parse_tpo(req.text)
    return {"parsed_tpo": state["parsed_tpo"]}

@app.post("/step/recommend")
def recommend(session_id: str):
    state = get_session(session_id)
    
    category = state["current_step"]
    db_path = f"./db/{category}" 
    metadata = load_metadata(db_path)
    index = load_faiss_index(db_path)

    context = (
        state["persona"]["선호 스타일"] + " " +
        state["persona"]["선호 아이템"] + " " +
        " ".join(state["parsed_tpo"]) + " " +
        " ".join(state["selected_items"])
    )
    query_emb = clip_embed(context)

    items = retrieve(
        metadata=metadata,
        index=index,
        query_emb=query_emb,
        category=category,
        negative=state.get("negative", {})
    )

    return {
        "category": category,
        "items": [
            {
                "item_id": it["product_id"],
                "image": it["image_url"],
                "description": it["description"], 
                "reason": generate_reason(it["description"], context)
            } for it in items
        ]
    }

@app.post("/step/select")
def select_item(req: SelectReq):
    state = get_session(req.session_id)
    state["selected_items"].append(req.item_id)

    idx = CATEGORY_ORDER.index(state["current_step"])
    if idx + 1 < len(CATEGORY_ORDER):
        state["current_step"] = CATEGORY_ORDER[idx + 1]

    return {"next_category": state["current_step"]}

@app.get("/lookbook")
def lookbook(session_id: str):
    state = get_session(session_id)
    return {"items": state["selected_items"]}
