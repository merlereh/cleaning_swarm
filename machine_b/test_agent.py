import json

import ollama

import rag

MODEL = "qwen3-vl:4b-instruct"  

THINK = "instruct" not in MODEL

# The tool as the LLM sees it: name, description, parameters
TOOLS = [{
    "type": "function",
    "function": {
        "name": "assign_task",
        "description": "Assign one cleaning step to one robot. Returns the new task_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string"},
                "action": {"type": "string", "enum": ["vacuum", "mop"]},
                "x": {"type": "number"},
                "y": {"type": "number"},
                "after": {"type": "string", "description": "task_id that must finish first, if any"},
            },
            "required": ["robot_id", "action", "x", "y"],
        },
    },
}]

plan: list[dict] = []


def assign_task(robot_id: str, action: str, x: float, y: float, after: str | None = None) -> dict:
    """Our code executes the tool - and checks the hard rules before accepting it."""
    robot = next((r for r in rag.knowledge["robots"] if r["id"] == robot_id), None)
    if robot is None:
        return {"error": f"unknown robot {robot_id}"}
    if action not in robot["can"]:
        return {"error": f"{robot_id} cannot {action}"}
    room = rag.room_at(x, y)
    if room is None:
        return {"error": "location is outside the flat"}
    if action == "mop" and room["floor"] == "carpet":
        return {"error": "mopping on carpet is forbidden"}
    if after and after not in [t["task_id"] for t in plan]:
        known = ", ".join(t["task_id"] for t in plan) or "none"
        return {"error": f"unknown task '{after}'. Existing task_ids: {known}"}
    task = {"task_id": f"t{len(plan)}", "robot_id": robot_id, "action": action,
            "x": x, "y": y, "room": room["name"], "after": after or None}
    plan.append(task)
    return {"ok": True, "task_id": task["task_id"]}


SYSTEM = """You coordinate household cleaning robots.
For each dirt detection, call assign_task once per cleaning step.
If a step must wait for another step at the same spot, pass the earlier task_id as `after`.
Use the exact task_id string returned by assign_task, for example "t0".
Follow the facts given for each detection exactly.
If assign_task returns an error, fix the problem and try again.
When every detection is handled, reply with a short summary and no tool call."""

DETECTIONS = [
    {"x": 1.5, "y": 1.0, "dirt_type": "dry"},  # kitchen
    {"x": 5.0, "y": 2.0, "dirt_type": "dry"},  # living room
    {"x": 1.0, "y": 4.5, "dirt_type": "wet"},  # bathroom
]

# 1. Classic RAG: look up the facts for every detection before the agent starts
rag.build()
blocks = []
for i, det in enumerate(DETECTIONS):
    result = rag.context_for(det)
    if result is None:
        continue
    room, facts = result
    blocks.append(f"Detection {i}: {det['dirt_type']} dirt in the {room} "
                  f"at x={det['x']}, y={det['y']}.\nFacts:\n{facts}")

messages = [
    {"role": "system", "content": SYSTEM},
    {"role": "user", "content": "\n\n".join(blocks)},
]

# 2. Agent loop: LLM asks for tool calls, our code executes them
errors: list[str] = []

for step in range(15):
    response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS,
                           think=THINK, options={"temperature": 0})
    messages.append(response.message)

    if not response.message.tool_calls:
        print("\nAgent:", response.message.content or "(no text)")
        print("Thinking:", (response.message.thinking or "(none)")[:1000])

        if errors or not plan:
            if not plan:
                errors.append("You have not assigned any task yet. "
                              "Call assign_task for every detection.")
            reminder = ("These problems are still open:\n"
                        + "\n".join(errors)
                        + "\nFix them now. If you already fixed them, reply 'done'.")
            print("\n[reminder]\n" + reminder + "\n")
            messages.append({"role": "user", "content": reminder})
            errors = []
            continue
        break

    for call in response.message.tool_calls:
        try:
            result = assign_task(**call.function.arguments)
        except TypeError as e:
            result = {"error": f"bad arguments: {e}"}
        print(f"{call.function.name}({call.function.arguments}) -> {result}")
        if "error" in result:
            errors.append(f"{call.function.name}({call.function.arguments}) -> {result['error']}")
        messages.append({"role": "tool", "content": json.dumps(result),
                         "tool_name": call.function.name})

print("\nFinal plan:")
for task in plan:
    print(" ", task)