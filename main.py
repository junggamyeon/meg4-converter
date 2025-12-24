import os
import re
import glob
import json
import base64
import shutil
import dotenv
import zipfile
from PIL import Image
from io import BytesIO

from utils.model import Model
from utils.texture import Texture
from utils.animation import Animation

print("Starting convert")
dotenv.load_dotenv()

# Recreate working directories
for d in ("output", "blueprints"):
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)

# Load zip from local path (GitHub Action will download it)
bpfile = os.getenv("file")
if not bpfile or not os.path.exists(bpfile):
    print("Blueprint zip not found")
    raise SystemExit(1)

with zipfile.ZipFile(bpfile, "r") as zf:
    zf.extractall("blueprints/")
print("Blueprints extracted")

# Convert all bbmodel files
for modelfile in glob.glob("blueprints/**/*.bbmodel", recursive=True):
    print(f"Convert file: {modelfile}")

    with open(modelfile, "r", encoding="utf-8") as f:
        data = json.load(f)

    name = os.path.splitext(modelfile)[0] \
        .replace("blueprints/", "") \
        .replace("\\", "/") \
        .replace("/", "_")

    outdir = f"output/{name}"
    os.makedirs(outdir, exist_ok=True)

    textures = {"width": 0, "height": 0, "data": {}}
    model_texture = None

    for slot, tex in enumerate(data.get("textures", [])):
        src = tex.get("source", "")
        tex_data = re.sub(r"^data:image/.+;base64,", "", src)
        img = Image.open(BytesIO(base64.b64decode(tex_data)))

        frame_time = int(tex.get("frame_time", 1) or 1)
        if frame_time > 1:
            h = img.height // frame_time
            img = img.crop((0, 0, img.width, h))

        textures["data"][str(slot)] = {
            "image": img,
            "position": textures["height"]
        }
        textures["width"] = max(textures["width"], img.width)
        textures["height"] += img.height

    if textures["data"]:
        model_texture = Image.new("RGBA", (textures["width"], textures["height"]))
        y = 0
        for t in textures["data"].values():
            model_texture.paste(t["image"], (0, y))
            y += t["image"].height

        model_texture.save(f"{outdir}/{name}.png")

    texture = Texture(model_texture, textures) if model_texture else None

    model = Model(
        data,
        texture,
        identifier=f"geometry.{name}"
    ).to_geometry_bedrock()

    animations = Animation(data.get("animations", [])).to_bedrock()

    with open(f"{outdir}/{name}.geo.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=4)

    with open(f"{outdir}/{name}.animation.json", "w", encoding="utf-8") as f:
        json.dump(animations, f, indent=4)

print("Convert done")
