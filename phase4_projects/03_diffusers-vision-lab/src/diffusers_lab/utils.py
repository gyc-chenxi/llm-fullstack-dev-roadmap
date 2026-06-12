from pathlib import Path
from PIL import Image
import numpy as np

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def load_rgb(path: str | Path, size: tuple[int, int] | None = None) -> Image.Image:
    img = Image.open(path).convert("RGB")
    if size is not None:
        img = img.resize(size)
    return img

def load_mask(path: str | Path, size: tuple[int, int] | None = None) -> Image.Image:
    img = Image.open(path).convert("L")
    if size is not None:
        img = img.resize(size)
    return img

def image_stats(image: Image.Image) -> dict:
    arr = np.array(image.convert("RGB"))
    return {
        "min": int(arr.min()),
        "max": int(arr.max()),
        "mean": round(float(arr.mean()), 3),
        "black_image": bool(arr.max() == 0),
    }
