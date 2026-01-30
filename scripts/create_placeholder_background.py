"""Create one placeholder background image (1080x1920) for demo when no API keys."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image
import numpy as np

W, H = 1080, 1920
out = ROOT / "assets" / "backgrounds" / "placeholder.jpg"
out.parent.mkdir(parents=True, exist_ok=True)

# Dark gradient (top darker, slight blue)
arr = np.zeros((H, W, 3), dtype=np.uint8)
for y in range(H):
    t = y / H
    r = int(15 + 10 * (1 - t))
    g = int(18 + 12 * (1 - t))
    b = int(28 + 15 * (1 - t))
    arr[y, :] = [r, g, b]

img = Image.fromarray(arr)
img.save(out, quality=85)
print(f"Created {out}")
