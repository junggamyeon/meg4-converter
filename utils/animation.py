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
            raw_name = anim.get("name", "unnamed")
            bedrock_name = self.__bedrock_name(raw_name, self.namespace)

            entry = {
                "loop": self.__loop_value(anim.get("loop", "once")),
                "bones": {}
            }

            # Giữ logic cũ: copy raw bone structure
            for bone_name, bone_data in anim.get("bones", {}).items():
                if not isinstance(bone_data, dict):
                    continue

                bone_entry = {}

                for channel, timeline in bone_data.items():
                    if channel not in ("rotation", "position", "scale"):
                        continue

                    if isinstance(timeline, dict) and timeline:
                        bone_entry[channel] = timeline

                if bone_entry:
                    entry["bones"][bone_name] = bone_entry

            # Nếu animation thật sự không có bone → bỏ qua animation này
            if not entry["bones"]:
                continue

            data["animations"][bedrock_name] = entry

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
