import os
import re
import glob
import json
import base64
import shutil
import dotenv
import zipfile
import urllib.request
from PIL import Image
from io import BytesIO

from utils.model import Model
from utils.texture import Texture
from utils.animation import Animation

print("Starting convert")
dotenv.load_dotenv()

# Recreate working directories
for i in ("output", "blueprints"):
    if os.path.exists(i) and (os.getenv("file") or i == "output"):
        shutil.rmtree(i)
    os.makedirs(i, exist_ok=True)

# Optional: load a zip of bbmodels into blueprints/
if os.getenv("file"):
    if os.getenv("file").startswith("http"):
        with urllib.request.urlopen(os.getenv("file")) as res:
            with open("blueprints/download.zip", "wb") as f:
                f.write(res.read())
                bpfile = "blueprints/download.zip"
    elif os.getenv("file").endswith(".zip") and os.path.exists(os.getenv("file")):
        bpfile = os.getenv("file")
    else:
        print("File not found")
        raise SystemExit(404)

    with zipfile.ZipFile(bpfile, "r") as zf:
        zf.extractall("blueprints/")
    print("Loaded blueprints")

# Convert every .bbmodel
for modelfile in glob.glob("blueprints/**/*.bbmodel", recursive=True):
    print(f"Convert file: {modelfile}")

    with open(modelfile, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build a single texture atlas (stack textures vertically)
    textures = {"width": 0, "height": 0, "data": {}}
    name = os.path.splitext(modelfile)[0].replace("blueprints/", "").replace("\\", "/").replace("/", "_")
    outdir = f"output/{name}"
    os.makedirs(outdir, exist_ok=True)

    model_texture = None

    for slot, tex in enumerate(data.get("textures", [])):
        src = tex.get("source", "")
        texture_data = re.sub(r'^data:image/.+;base64,', '', src)
        texture_image = Image.open(BytesIO(base64.b64decode(texture_data)))

        # Remove animation frames (keep first frame) if present
        frame_time = int(tex.get("frame_time", 1) or 1)
        if frame_time > 1:
            height = texture_image.height // frame_time
            texture_image = texture_image.crop((0, 0, texture_image.width, height))

        textures["data"][str(slot)] = {"image": texture_image, "position": textures["height"]}
        textures["width"] = max(textures["width"], texture_image.width)
        textures["height"] += texture_image.height

    if data.get("textures"):
        model_texture = Image.new("RGBA", (textures["width"], textures["height"]))
        y = 0
        for _, texinfo in textures["data"].items():
            model_texture.paste(texinfo["image"], (0, y))
            y += texinfo["image"].height
        model_texture.save(f"{outdir}/{name}.png")

    texture = Texture(model_texture, textures) if data.get("textures") else None

    # Convert model + animations
    animations = Animation(data.get("animations", [])).to_bedrock()
    model = Model(data, texture, identifier=f"geometry.{name}").to_geometry_bedrock()

    # Write files (Bedrock-friendly names)
    with open(f"{outdir}/{name}.geo.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=4)
    with open(f"{outdir}/{name}.animation.json", "w", encoding="utf-8") as f:
        json.dump(animations, f, indent=4)

    # Keep legacy filenames for compatibility with your old workflow
    with open(f"{outdir}/{name}.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=4)
    with open(f"{outdir}/animation.{name}.json", "w", encoding="utf-8") as f:
        json.dump(animations, f, indent=4)

print("Convert done")
