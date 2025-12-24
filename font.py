# font.py
import os
import sys
import json
from utils.font import collect_png, pack_sheet, chunk

UNICODE_START = 0xE000
MAX_GLYPHS = 256

def run(input_dir: str, output_dir: str):
    images = collect_png(input_dir)
    if not images:
        raise RuntimeError("No valid PNG files found")

    font_dir = os.path.join(output_dir, "fonts")
    os.makedirs(font_dir, exist_ok=True)

    providers = []
    codepoint = UNICODE_START
    sheet_index = 0

    for group in chunk(images, MAX_GLYPHS):
        sheet_name = f"glyph_E{sheet_index}.png"
        sheet_path = os.path.join(font_dir, sheet_name)

        w, h = pack_sheet(group, sheet_path)
        if w == 0 or h == 0:
            continue

        chars = []
        for _ in group:
            chars.append(chr(codepoint))
            codepoint += 1

        providers.append({
            "type": "bitmap",
            "file": sheet_name,
            "height": h,
            "ascent": max(0, int(h * 0.85)),
            "chars": chars
        })

        sheet_index += 1

    with open(os.path.join(font_dir, "default.json"), "w", encoding="utf-8") as f:
        json.dump({"providers": providers}, f, indent=2, ensure_ascii=False)

    print(f"[OK] Generated {sheet_index} font sheets")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python font.py <input_dir> <output_dir>")
        raise SystemExit(1)
    run(sys.argv[1], sys.argv[2])
