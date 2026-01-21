from __future__ import annotations


class Animation:
    def __init__(self, animations: list, namespace: str = "ancient") -> None:
        self.animations = animations or []
        self.namespace = namespace

    @staticmethod
    def __bedrock_name(raw_name: str, namespace: str) -> str:
        name = raw_name.replace(" ", "_").lower()
        return f"animation.{namespace}.{name}"

    @staticmethod
    def __get_loop(loop: str):
        if loop == "loop":
            return True
        if loop == "once":
            return False
        if loop == "hold":
            return "hold_on_last_frame"
        return False

    @staticmethod
    def __vec3(dp: dict):
        if not isinstance(dp, dict):
            return None
        if all(k in dp for k in ("x", "y", "z")):
            return [float(dp["x"]), float(dp["y"]), float(dp["z"])]
        return None

    @staticmethod
    def __animators_to_bones(animators: dict) -> dict:
        out = {}
        if not isinstance(animators, dict):
            return out

        for _, animator in animators.items():
            if not isinstance(animator, dict):
                continue

            bone_name = animator.get("name") or animator.get("uuid") or "bone"
            kfs = animator.get("keyframes") or []
            if not isinstance(kfs, list):
                continue

            bone = out.setdefault(bone_name, {})

            for kf in kfs:
                if not isinstance(kf, dict):
                    continue

                channel = kf.get("channel")
                t = kf.get("time")

                if channel not in ("rotation", "position", "scale") or t is None:
                    continue

                dps = kf.get("data_points") or kf.get("dataPoints") or []
                vec = None

                if isinstance(dps, list) and dps:
                    vec = Animation.__vec3(dps[0])

                if vec is None:
                    vec = Animation.__vec3(kf)

                if vec is None:
                    continue

                ch = bone.setdefault(channel, {})
                ch[str(float(t))] = vec

        return out

    def to_bedrock(self) -> dict:
        data = {
            "format_version": "1.8.0",
            "animations": {}
        }

        for anim in self.animations:
            if not isinstance(anim, dict):
                continue

            raw_name = anim.get("name") or "converted"
            name = self.__bedrock_name(raw_name, self.namespace)

            loop = self.__get_loop(anim.get("loop", "loop"))
            length = anim.get("length", anim.get("animation_length"))
            animators = anim.get("animators", {})

            bones = self.__animators_to_bones(animators)
            if not bones:
                continue

            entry = {
                "loop": loop,
                "bones": bones
            }

            if length is not None:
                entry["animation_length"] = float(length)

            for k in ("anim_time_update", "blend_weight", "start_delay", "loop_delay"):
                if k in anim and anim[k] is not None:
                    entry[k] = anim[k]

            data["animations"][name] = entry

        return data
