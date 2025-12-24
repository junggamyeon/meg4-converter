from __future__ import annotations
from utils.texture import Texture

class Model:
    def __init__(self, data: dict, texture: Texture | None = None, identifier: str = "geometry.converted") -> None:
        self.elements = self.__sort_elements(data.get("elements", []))
        self.outliner = data.get("outliner", [])
        self.texture = texture
        self.identifier = identifier
        self.bones: list[dict] = []

    @staticmethod
    def __sort_elements(elements: list) -> list:
        try:
            return sorted(elements, key=lambda x: x.get("uuid", ""))
        except Exception:
            return elements

    @staticmethod
    def __bb_to_bedrock_pivot(pivot):
        # Blockbench -> Bedrock coordinate pivot transform
        # x is flipped
        if not pivot or not isinstance(pivot, (list, tuple)) or len(pivot) < 3:
            return [0, 0, 0]
        return [-float(pivot[0]), float(pivot[1]), float(pivot[2])]

    def __get_rotation_payload(self, element: dict) -> dict | None:
        """
        Supports both bbmodel rotation formats:
        A) rotation as dict: {"origin":[...], "axis":"x|y|z", "angle":deg}
        B) rotation as list: [x,y,z] and element has origin (pivot) in element["origin"]
        """
        rot = element.get("rotation")

        # No rotation
        if rot is None:
            return None

        # Format B: list [x, y, z]
        if isinstance(rot, (list, tuple)) and len(rot) >= 3:
            pivot = element.get("origin") or element.get("pivot") or [0, 0, 0]
            return {
                "pivot": self.__bb_to_bedrock_pivot(pivot),
                "rotation": [float(rot[0]), float(rot[1]), float(rot[2])]
            }

        # Format A: dict {"origin","axis","angle"}
        if isinstance(rot, dict):
            origin = rot.get("origin") or element.get("origin") or [0, 0, 0]
            axis = rot.get("axis")
            angle = rot.get("angle")

            if axis is None or angle is None:
                return None

            r = [0.0, 0.0, 0.0]
            if axis == "x":
                r[0] = float(angle)
            elif axis == "y":
                r[1] = float(angle)
            elif axis == "z":
                r[2] = float(angle)

            return {
                "pivot": self.__bb_to_bedrock_pivot(origin),
                "rotation": r
            }

        # Unknown type -> ignore rotation instead of crashing
        return None

    def __element_to_cube(self, element: dict) -> dict:
        frm = element.get("from", [0, 0, 0])
        to = element.get("to", [0, 0, 0])

        cube = {
            "origin": [-to[0], frm[1], frm[2]],
            "size": [to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]],
        }

        # UV mapping
        if self.texture and element.get("faces"):
            uv = {}
            for face_name, face in element["faces"].items():
                mapped = self.texture.get_uv(face_name, face)
                if mapped:
                    uv[face_name] = mapped
            if uv:
                cube["uv"] = uv

        # Rotation (safe)
        rot_payload = self.__get_rotation_payload(element)
        if rot_payload:
            cube.update(rot_payload)

        # Inflate (optional)
        if element.get("inflate") not in (None, 0, 0.0):
            cube["inflate"] = float(element["inflate"])

        return cube

    def outliner_worker(self, group: dict, outliner: list, parent: str | None = None) -> None:
        for i in outliner:
            # Group node
            if isinstance(i, dict) and i.get("children") is not None:
                bone = {"name": i.get("name", "bone"), "pivot": [0, 0, 0]}
                if parent:
                    bone["parent"] = parent

                pivot = i.get("origin") or i.get("pivot")
                if pivot:
                    bone["pivot"] = self.__bb_to_bedrock_pivot(pivot)

                cubes = []
                for child in i.get("children", []):
                    if isinstance(child, str):
                        el = next((e for e in self.elements if e.get("uuid") == child), None)
                        if el:
                            cubes.append(self.__element_to_cube(el))

                if cubes:
                    bone["cubes"] = cubes

                self.bones.append(bone)

                nested = [c for c in i.get("children", []) if isinstance(c, dict)]
                if nested:
                    self.outliner_worker({}, nested, bone["name"])

            # Direct element uuid at root
            elif isinstance(i, str):
                el = next((e for e in self.elements if e.get("uuid") == i), None)
                if el:
                    root_bone = {"name": "bones", "pivot": [0, 0, 0], "cubes": [self.__element_to_cube(el)]}
                    if root_bone not in self.bones:
                        self.bones.append(root_bone)

    def to_geometry_bedrock(self) -> dict:
        geometry = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": self.identifier,
                        "texture_width": self.texture.image.width if self.texture else 0,
                        "texture_height": self.texture.image.height if self.texture else 0
                    },
                    "bones": []
                }
            ]
        }

        self.bones = []
        self.outliner_worker({"name": "bones", "pivot": [0, 0, 0], "cubes": []}, self.outliner)

        if not any(b.get("name") == "bones" for b in self.bones):
            self.bones.insert(0, {"name": "bones", "pivot": [0, 0, 0]})

        geometry["minecraft:geometry"][0]["bones"] = self.bones
        return geometry
