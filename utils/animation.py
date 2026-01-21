import json


class Animation:

    def __init__(self, animations: list, namespace: str = "ancient") -> None:
        self.animations = animations or []
        self.namespace = namespace

    @staticmethod
    def __bedrock_name(raw_name: str, namespace: str):
        clean = raw_name.replace(" ", "_").lower()
        return f"animation.{namespace}.{clean}"

    @staticmethod
    def __loop_value(loop: str):
        if loop == "loop":
            return True
        if loop == "once":
            return False
        if loop == "hold":
            return "hold_on_last_frame"
        return False

    def export(self, path: str):
        data = {
            "format_version": "1.8.0",
            "animations": {}
        }

        for anim in self.animations:
            name = anim.get("name", "unnamed")
            bedrock_name = self.__bedrock_name(name, self.namespace)

            entry = {
                "loop": self.__loop_value(anim.get("loop", "once")),
                "bones": {}
            }

            for bone in anim.get("bones", []):
                bone_name = bone.get("name", "root")
                frames = bone.get("keyframes", [])

                bone_entry = {}

                for frame in frames:
                    channel = frame.get("channel")

                    if channel not in ("rotation", "position", "scale"):
                        continue

                    time = str(frame.get("time", 0))
                    value = frame.get("value", [0, 0, 0])

                    if channel not in bone_entry:
                        bone_entry[channel] = {}

                    bone_entry[channel][time] = value

                if bone_entry:
                    entry["bones"][bone_name] = bone_entry

            data["animations"][bedrock_name] = entry

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
