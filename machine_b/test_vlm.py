import subprocess
import time
from pathlib import Path

from vlm import MODEL, detect_dirt, load_small, warmup

# 1. Modell entladen -> leert Ollamas Prompt-Cache, jeder Lauf ist ein ehrlicher Kaltstart
subprocess.run(["ollama", "stop", MODEL], capture_output=True)

# 2. Warm-up -> Ladezeit fällt hier an und nicht beim ersten Testbild
print(f"Modell: {MODEL}")
start = time.time()
warmup()
print(f"Warm-up (Modell laden): {time.time() - start:.1f} s\n")

# 3. Eigentlicher Test
correct = 0
times = []
images = sorted(Path("machine_b/images").glob("*.jpeg"))
for image in images:
    start = time.time()
    report = detect_dirt(load_small(image), verbose=True)
    elapsed = time.time() - start
    times.append(elapsed)

    expected = image.name.startswith("dirt")
    ok = report.dirty == expected
    correct += ok
    print(f"{'OK  ' if ok else 'FAIL'} {image.name} ({elapsed:.1f} s)")
    print(f"     {report}\n")

print(f"{correct}/{len(images)} correct | "
      f"Ø {sum(times) / len(times):.1f} s pro Bild")