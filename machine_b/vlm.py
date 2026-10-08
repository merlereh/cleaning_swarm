import io
from pathlib import Path
from typing import Literal

import ollama
from PIL import Image
from pydantic import BaseModel

MODEL = "qwen3-vl:4b-instruct"

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


def load_small(path: Path, max_size: int = 640) -> bytes:
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_size, max_size))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def detect_dirt(image: bytes, verbose: bool = False) -> DirtReport:
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT, "images": [image]}],
        format=DirtReport.model_json_schema(),
        options={"temperature": 0, "num_predict": 60},
        think=False,
        keep_alive="30m",  # Modell zwischen den Aufrufen im Speicher halten
    )
    if verbose:
        r = response
        print(f"load {r.load_duration/1e9:.1f}s | "
              f"prompt {r.prompt_eval_count} tok in {r.prompt_eval_duration/1e9:.1f}s | "
              f"output {r.eval_count} tok in {r.eval_duration/1e9:.1f}s")
        print(f"thinking: {len(r.message.thinking or '')} Zeichen | "
              f"content: {len(r.message.content)} Zeichen")
        print(repr(r.message.content[:300]))
    return DirtReport.model_validate_json(response.message.content)


def warmup() -> None:
    """Lädt das Modell mit einem Dummy-Bild, damit der erste echte Aufruf
    nicht die Ladezeit bezahlt. Das Dummy-Bild ist bewusst kein echtes Bild,
    damit kein Testbild im Prompt-Cache landet."""
    dummy = Image.new("RGB", (640, 480), (128, 100, 70))
    buf = io.BytesIO()
    dummy.save(buf, format="JPEG")
    detect_dirt(buf.getvalue())