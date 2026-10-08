import json
from pathlib import Path

import chromadb
import ollama

EMBED_MODEL = "nomic-embed-text"
HERE = Path(__file__).parent
knowledge = json.loads((HERE / "knowledge.json").read_text())

db = chromadb.PersistentClient(path=str(HERE / "chroma_db"))
collection = db.get_or_create_collection("household", metadata={"hnsw:space": "cosine"})


def embed(texts: list[str], prefix: str) -> list[list[float]]:
    # nomic-embed-text works best with these task prefixes
    return ollama.embed(model=EMBED_MODEL, input=[prefix + t for t in texts]).embeddings


def _documents() -> list[dict]:
    """Turn knowledge.json into small text chunks, one per room, robot and rule."""
    docs = []
    for r in knowledge["rooms"]:
        text = (f"The {r['name']} has a {r['floor']} floor. It spans x from "
                f"{r['x'][0]} to {r['x'][1]} m and y from {r['y'][0]} to {r['y'][1]} m.")
        docs.append({"id": f"room:{r['name']}", "kind": "room", "text": text})
    for rb in knowledge["robots"]:
        docs.append({"id": f"robot:{rb['id']}", "kind": "robot", "text": rb["text"]})
    for i, rule in enumerate(knowledge["rules"]):
        docs.append({"id": f"rule:{i}", "kind": "rule", "text": rule})
    return docs


def build() -> int:
    """(Re)build the vector database from knowledge.json."""
    old = collection.get()["ids"]
    if old:
        collection.delete(ids=old)
    docs = _documents()
    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[{"kind": d["kind"]} for d in docs],
        embeddings=embed([d["text"] for d in docs], "search_document: "),
    )
    return len(docs)


def retrieve(query: str, kind: str, k: int) -> list[str]:
    """The k facts of one kind that are most similar to the query."""
    result = collection.query(
        query_embeddings=embed([query], "search_query: "),
        n_results=k,
        where={"kind": kind},
    )
    return result["documents"][0]


def room_at(x: float, y: float) -> dict | None:
    """Pure geometry: which room contains this point?"""
    for r in knowledge["rooms"]:
        if r["x"][0] <= x < r["x"][1] and r["y"][0] <= y < r["y"][1]:
            return r
    return None


def context_for(detection: dict) -> tuple[str, str] | None:
    """Classic RAG retrieval for one dirt detection: returns (room name, facts)."""
    room = room_at(detection["x"], detection["y"])
    if room is None:
        return None
    room_facts = retrieve(f"{room['name']} floor type", "room", k=1)
    rule_facts = retrieve(
        f"cleaning rules: {room_facts[0]} {detection['dirt_type']} dirt", "rule", k=2
    )
    robot_facts = [rb["text"] for rb in knowledge["robots"]]  # always needed
    facts = "\n".join(f"- {f}" for f in room_facts + rule_facts + robot_facts)
    return room["name"], facts