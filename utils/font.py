# ultis/font.py
import os
import math
from PIL import Image

PNG_SIG = b"\x89PNG\r\n\x1a\n"

def _is_real_png(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(8) == PNG_SIG
    except Exception:
        return False

def collect_png(root: str):
    out = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__MACOSX"]
        for f in files:
            if f.startswith("._"):
                continue
            if not f.lower().endswith(".png"):
                continue
            full = os.path.join(r, f)
            if not _is_real_png(full):
                continue
            out.append(full)
    return sorted(out)

def chunk(arr, size: int):
    for i in range(0, len(arr), size):
        yield arr[i:i + size]

def _calc_grid(n: int):
    cols = math.ceil(math.sqrt(n)) if n > 0 else 0
    rows = math.ceil(n / cols) if cols > 0 else 0
    return cols, rows

def pack_sheet(images, out_path: str):
    if not images:
        return 0, 0

    first = Image.open(images[0]).convert("RGBA")
    w, h = first.size
    if w <= 0 or h <= 0:
        return 0, 0

    cols, rows = _calc_grid(len(images))
    if cols <= 0 or rows <= 0:
        return 0, 0

    sheet = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))

    for i, img_path in enumerate(images):
        img = Image.open(img_path).convert("RGBA")
        if img.size != (w, h):
            img = img.resize((w, h), Image.NEAREST)
        x = (i % cols) * w
        y = (i // cols) * h
        sheet.paste(img, (x, y))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    return w, h
