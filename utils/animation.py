from __future__ import annotations

class Animation:
    """
    Convert Blockbench bbmodel animations -> Bedrock animation json.
    We aim for Bedrock 1.20+ compatibility by emitting a stable RP animation schema.
    """
    def __init__(self, animations: list) -> None:
        self.animations = animations or []

    @staticmethod
    def __get_loop(loop: str):
        # Bedrock supports: true, false, "hold_on_last_frame"
        if loop in ("loop", "once"):
            return True
        if loop == "hold":
            return "hold_on_last_frame"
        return True

    @staticmethod
    def __vec3(dp: dict):
        if not isinstance(dp, dict):
            return None
        if all(k in dp for k in ("x", "y", "z")):
            return [float(dp["x"]), float(dp["y"]), float(dp["z"])]
        return None

    @staticmethod
    def __animators_to_bones(animators: dict) -> dict:
        """
        Blockbench animator structure varies a bit across versions.
        We try to be permissive:
          animators: { "<uuid>": { "name": "bone", "keyframes": [...] }, ... }
        Each keyframe typically has:
          channel: "rotation"|"position"|"scale"
          time: float
          data_points: [{x,y,z}, ...]  (we take the first)
        """
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
                    # Some bbmodel versions store values directly
                    vec = Animation.__vec3(kf)  # tries x,y,z on keyframe itself
                if vec is None:
                    continue

                ch = bone.setdefault(channel, {})
                # Bedrock time keys are strings
                ch[str(float(t))] = vec

        return out

    def to_bedrock(self) -> dict:
        data = {"format_version": "1.8.0", "animations": {}}
        for anim in self.animations:
            if not isinstance(anim, dict):
                continue
            name = anim.get("name") or "animation.converted"
            loop = self.__get_loop(anim.get("loop", "loop"))
            length = anim.get("length", anim.get("animation_length"))
            animators = anim.get("animators", {})

            entry = {
                "loop": loop,
                "bones": self.__animators_to_bones(animators),
            }
            if length is not None:
                entry["animation_length"] = float(length)

            # Pass through optional fields if they exist (won't break if ignored)
            for k in ("anim_time_update", "blend_weight", "start_delay", "loop_delay"):
                if k in anim and anim[k] is not None:
                    entry[k] = anim[k]

            data["animations"][name] = entry

        return data
