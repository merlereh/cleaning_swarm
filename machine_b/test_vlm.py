import time
from pathlib import Path

from vlm import detect_dirt, load_small

correct = 0
images = sorted(Path("machine_b/images").glob("*.jpeg"))
for image in images:
    start = time.time()
    report = detect_dirt(load_small(image))
    expected = image.name.startswith("dirt")
    ok = report.dirty == expected
    correct += ok
    print(f"{'OK  ' if ok else 'FAIL'} {image.name} ({time.time() - start:.1f} s)")
    print(f"     {report}\n")

print(f"{correct}/{len(images)} correct")