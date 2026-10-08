import ollama

import rag

MODEL = "qwen3-vl:4b-instruct"

print("Facts in database:", rag.build())

DETECTIONS = [
    {"x": 1.5, "y": 1.0, "dirt_type": "dry"},  # kitchen
    {"x": 5.0, "y": 2.0, "dirt_type": "dry"},  # living room
    {"x": 1.0, "y": 4.5, "dirt_type": "wet"},  # bathroom
]

for det in DETECTIONS:
    result = rag.context_for(det)
    if result is None:
        print(f"({det['x']}, {det['y']}) is outside the flat, skipping\n")
        continue
    room, facts = result

    prompt = f"""Dirt ({det['dirt_type']}) was detected in the {room} at x={det['x']}, y={det['y']}.
Using only these facts:
{facts}

Which robot(s) should clean it, and in which order? Answer in one or two sentences."""

    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    print(f"=== {room} (x:{det['x']}, y:{det['y']}, dirt:{det['dirt_type']}) ===")
    print("Retrieved facts:\n" + facts)
    print("Answer:", response.message.content, "\n")