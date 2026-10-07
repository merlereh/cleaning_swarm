import io
from pathlib import Path
from typing import Literal

import ollama
from PIL import Image
from pydantic import BaseModel

MODEL = "qwen3-vl:8b"  # your variant without thinking

PROMPT = """You are the camera of a household cleaning robot looking at the floor.
Decide if there is dirt ON the floor: crumbs, dust, stains, spilled liquid.
These are NOT dirt: wood grain, gaps between planks, grout lines, shadows, reflections.
Only answer dirty=true if you see actual dirt.
If there is dirt, say where it is in the image:
- horizontal: left, center or right
- distance: near (bottom third of the image), middle, or far (top third)
If there is no dirt, use "none" for both."""


class DirtReport(BaseModel):
    dirty: bool
    dirt_type: Literal["none", "dry", "wet"]
    horizontal: Literal["none", "left", "center", "right"]
    distance: Literal["none", "near", "middle", "far"]
    description: str


def load_small(path: Path, max_size: int = 640) -> bytes:
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_size, max_size))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def detect_dirt(image: bytes) -> DirtReport:
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT, "images": [image]}],
        format=DirtReport.model_json_schema(),
        options={"temperature": 0},
    )
    return DirtReport.model_validate_json(response.message.content)