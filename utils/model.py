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
        # Keep stable ordering; bbmodel elements have "uuid"
        try:
            return sorted(elements, key=lambda x: x.get("uuid", ""))
        except Exception:
            return elements

    @staticmethod
    def __get_origin(from_to: tuple[list, list]) -> list:
        origin = [-from_to[1][0], from_to[0][1], from_to[0][2]]
        return origin

    @staticmethod
    def __get_rotation(rotation: dict) -> dict | None:
        if not rotation:
            return None
        origin = rotation.get("origin")
        axis = rotation.get("axis")
        angle = rotation.get("angle")
        if origin is None or axis is None or angle is None:
            return None
        # Bedrock cube rotation is per-axis degrees; Blockbench gives axis+angle
        rot = [0.0, 0.0, 0.0]
        if axis == "x":
            rot[0] = float(angle)
        elif axis == "y":
            rot[1] = float(angle)
        elif axis == "z":
            rot[2] = float(angle)
        return {"pivot": [-origin[0], origin[1], origin[2]], "rotation": rot}

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

        # Rotation (optional)
        rot = self.__get_rotation(element.get("rotation"))
        if rot:
            cube.update(rot)

        # Inflate (optional)
        if element.get("inflate"):
            cube["inflate"] = float(element["inflate"])

        return cube

    def outliner_worker(self, group: dict, outliner: list, parent: str | None = None) -> None:
        for i in outliner:
            # Group node
            if isinstance(i, dict) and i.get("children") is not None:
                bone = {"name": i.get("name", "bone"), "pivot": [0, 0, 0]}
                if parent:
                    bone["parent"] = parent
                pivot = i.get("origin")
                if pivot:
                    bone["pivot"] = [-pivot[0], pivot[1], pivot[2]]
                cubes = []
                # Children can be uuids referencing elements, or nested groups
                for child in i.get("children", []):
                    if isinstance(child, str):
                        el = next((e for e in self.elements if e.get("uuid") == child), None)
                        if el:
                            cubes.append(self.__element_to_cube(el))
                    elif isinstance(child, dict):
                        # nested group; handled below by recursion
                        pass
                if cubes:
                    bone["cubes"] = cubes
                self.bones.append(bone)
                # Recurse nested groups
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
        # Use a broadly compatible schema version for entity geometry
        # (format_version is NOT the game version.)
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
        # Build bones from outliner
        self.outliner_worker({"name": "bones", "pivot": [0, 0, 0], "cubes": []}, self.outliner)

        # Ensure there is at least a root bone if outliner did not create one
        if not any(b.get("name") == "bones" for b in self.bones):
            self.bones.insert(0, {"name": "bones", "pivot": [0, 0, 0]})

        geometry["minecraft:geometry"][0]["bones"] = self.bones
        return geometry
