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

for i in ("output", "blueprints"):
    if os.path.exists(i) and (os.getenv("file") or i == "output"):
        shutil.rmtree(i)
    os.makedirs(i, exist_ok=True)

if os.getenv("file"):
    if os.getenv("file").startswith("http"):
        with urllib.request.urlopen(os.getenv("file")) as res:
            with open("blueprints/download.zip", "wb") as f:
                f.write(res.read())
                bpfile = "blueprints/download.zip"
    elif os.getenv("file").endswith(".zip"):
        bpfile = os.getenv("file")
    else:
        print("File not found")
        exit(404)
    with zipfile.ZipFile(bpfile, "r") as zf:
        zf.extractall("blueprints/")
    print("Loaded blueprints")

for modelfile in glob.glob("blueprints/**/*.bbmodel", recursive=True):
    print(f"Convert file: {modelfile}")

    with open(modelfile, "r") as f:
        data = json.load(f)
    
    textures = {"width": 0, "height": 0, "data": {}}
    name = os.path.splitext(modelfile)[0].replace("blueprints/", "").replace("/", "_")
    os.makedirs(f"output/{name}/")

    for slot, texture in enumerate(data.get("textures", [])):
        texture_data = re.sub('^data:image/.+;base64,', '', texture["source"])
        texture_image = Image.open(BytesIO(base64.b64decode(texture_data)))
        
        #Remove Animtion Frame
        if texture.get("frame_time", 1) > 1:
            height = texture_image.height // texture.get("frame_time")
            texture_image = texture_image.crop((0, 0, texture_image.width, height))

        textures["data"][str(slot)] = {"image": texture_image,"position": textures.get("height",0)}
        textures["width"] = max(textures["width"], texture_image.width)
        textures["height"] += texture_image.height

    if data.get("textures", None):
        model_texture = Image.new("RGBA", (textures["width"], textures["height"]))
        model_texture_height = 0
        for k, texture_img in textures["data"].items():
            model_texture.paste(texture_img["image"], (0, model_texture_height))
            model_texture_height += texture_img["image"].height
        model_texture.save(f"output/{name}/{name}.png")

    texture = Texture(model_texture, textures) if data.get("textures", None) else None
    animations = Animation(data.get("animations", [])).to_bedrock()
    model = Model(data, texture).to_geometry_bedrock()
    with open(f"output/{name}/{name}.json", "w") as f:
        json.dump(model, f, indent=4)
    with open(f"output/{name}/animation.{name}.json", 'w') as f:
        json.dump(animations, f, indent=4)

print("Convert done")