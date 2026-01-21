import os
import re
import glob
import json
import base64
import shutil
import zipfile
import uuid
from io import BytesIO
from PIL import Image

from utils.model import Model
from utils.texture import Texture
from utils.animation import Animation

PACK_NAME = os.getenv("PACK_NAME", "Converted Meg4")
PACK_DESC = os.getenv("PACK_DESC", "Jung Ganmyeon moded")
PACK_UUID_1 = os.getenv("PACK_UUID_1", str(uuid.uuid4()))
PACK_UUID_2 = os.getenv("PACK_UUID_2", str(uuid.uuid4()))
PACK_VERSION = [1, 0, 0]


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def write_json(path: str, data: dict):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


print("Starting convert (Pack mode)")

for d in ("_work", "output_pack", "blueprints"):
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)

bpfile = os.getenv("file")
if not bpfile or not os.path.exists(bpfile):
    print("Blueprint zip not found")
    raise SystemExit(1)

with zipfile.ZipFile(bpfile, "r") as zf:
    zf.extractall("blueprints/")

print("Blueprints extracted")

pack_root = "output_pack"
ensure_dir(pack_root)

manifest = {
    "format_version": 2,
    "header": {
        "name": PACK_NAME,
        "description": PACK_DESC,
        "uuid": PACK_UUID_1,
        "version": PACK_VERSION,
        "min_engine_version": [1, 20, 0]
    },
    "modules": [
        {
            "type": "resources",
            "uuid": PACK_UUID_2,
            "version": PACK_VERSION
        }
    ]
}

write_json(os.path.join(pack_root, "manifest.json"), manifest)

geo_dir = os.path.join(pack_root, "models", "entity")
anim_dir = os.path.join(pack_root, "animations")
tex_dir = os.path.join(pack_root, "textures", "entity")

ensure_dir(geo_dir)
ensure_dir(anim_dir)
ensure_dir(tex_dir)

converted_any = False

for modelfile in glob.glob("blueprints/**/*.bbmodel", recursive=True):
    print(f"Convert file: {modelfile}")

    with open(modelfile, "r", encoding="utf-8") as f:
        data = json.load(f)

    name = os.path.splitext(modelfile)[0] \
        .replace("blueprints/", "") \
        .replace("\\", "/") \
        .replace("/", "_") \
        .lower()

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

        textures["data"][str(slot)] = {"image": img}
        textures["width"] = max(textures["width"], img.width)
        textures["height"] += img.height

    if textures["data"]:
        model_texture = Image.new("RGBA", (textures["width"], textures["height"]))
        y = 0

        for t in textures["data"].values():
            model_texture.paste(t["image"], (0, y))
            y += t["image"].height

        model_texture.save(os.path.join(tex_dir, f"{name}.png"))

    texture = Texture(model_texture, textures) if model_texture else None

    model = Model(data, texture, identifier=f"geometry.{name}").to_geometry_bedrock()
    write_json(os.path.join(geo_dir, f"{name}.geo.json"), model)

    animations = data.get("animations", [])
    if animations:
        anim_exporter = Animation(data.get("animations", []), namespace=name)
        animations = anim_exporter.to_bedrock()
        write_json(os.path.join(anim_dir, f"{name}.animation.json"), animations)
    converted_any = True

if not converted_any:
    print("No .bbmodel found in zip")
    raise SystemExit(2)

pack_zip = "Converted_Pack.mcpack"
if os.path.exists(pack_zip):
    os.remove(pack_zip)

with zipfile.ZipFile(pack_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(pack_root):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, pack_root)
            z.write(full, rel)

print(f"Done. Output: {pack_zip}")
