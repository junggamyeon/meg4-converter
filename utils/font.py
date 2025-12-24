import os
import math
from PIL import Image

def collect_png(root):
    out = []
    for r, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(".png"):
                out.append(os.path.join(r, f))
    return sorted(out)

def calc_grid(n):
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return cols, rows

def pack_sheet(images, out_path):
    if not images:
        return 0, 0

    first = Image.open(images[0]).convert("RGBA")
    w, h = first.size

    cols, rows = calc_grid(len(images))
    sheet = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))

    for i, img_path in enumerate(images):
        img = Image.open(img_path).convert("RGBA")
        x = (i % cols) * w
        y = (i // cols) * h
        sheet.paste(img, (x, y))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    return w, h

def chunk(arr, size):
    for i in range(0, len(arr), size):
        yield arr[i:i + size]
