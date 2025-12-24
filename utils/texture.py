from __future__ import annotations
from PIL.ImageFile import ImageFile

class Texture:
    """
    Handles UV mapping when we stack multiple Blockbench textures into 1 vertical atlas.
    main.py creates:
        textures = {"data": { "0": {"position": y0}, "1": {"position": y1}, ... } }
    Blockbench faces contain:
        face["uv"] = [u0, v0, u1, v1]
        face["texture"] = slot index (int)
    """
    def __init__(self, image: ImageFile, textures: dict) -> None:
        self.image = image
        self.textures = textures

    def get_uv(self, face_name: str, face: dict) -> dict | None:
        uv = face.get("uv")
        if not uv or len(uv) != 4:
            return None

        tex_slot = face.get("texture", 0)
        try:
            offset_y = self.textures["data"][str(tex_slot)]["position"]
        except Exception:
            offset_y = 0

        # Bedrock expects uv as [u, v] and uv_size as [w, h]
        u0, v0, u1, v1 = uv
        return {
            "uv": [u0, v0 + offset_y],
            "uv_size": [u1 - u0, v1 - v0]
        }
