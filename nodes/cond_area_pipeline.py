import math

import torch


class ConditioningPipelineSetArea:
    @classmethod
    def INPUT_TYPES(cls):
        float_xy = {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}
        float_wh = {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}
        float_s = {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.05}

        return {
            "required": {
                "conditioning": ("CONDITIONING",),
                "width": ("FLOAT", float_wh),
                "height": ("FLOAT", float_wh),
                "x": ("FLOAT", float_xy),
                "y": ("FLOAT", float_xy),
                "strength": ("FLOAT", float_s),
            },
            "optional": {
                "pipeline_in": ("CONDITIONING_PIPELINE",),
            },
        }

    NODE_ID = "ConditioningPipelineSetArea"
    NODE_NAME = "Conditioning Pipeline (Set Area)"
    CATEGORY = "LoRA Pipeline/Conditioning"
    RETURN_TYPES = ("CONDITIONING_PIPELINE",)
    RETURN_NAMES = ("pipeline_out",)
    FUNCTION = "run"

    def _validate_area(self, idx, x, y, w, h, s):
        if not (0.0 <= x <= 1.0):
            raise RuntimeError(f"Area {idx}: x invalid")
        if not (0.0 <= y <= 1.0):
            raise RuntimeError(f"Area {idx}: y invalid")
        if w < 0.0:
            raise RuntimeError(f"Area {idx}: width invalid")
        if h < 0.0:
            raise RuntimeError(f"Area {idx}: height invalid")
        if x + w > 1.0 or y + h > 1.0:
            raise RuntimeError(f"Area {idx}: bounds exceeded")
        return True

    def run(
        self,
        conditioning,
        x=0.0,
        y=0.0,
        width=1.0,
        height=1.0,
        strength=1.0,
        pipeline_in=None,
    ):
        entries = list(pipeline_in) if pipeline_in is not None else []
        self._validate_area(len(entries) + 1, x, y, width, height, strength)

        entry = {
            "conditioning": conditioning,
            "x": float(x),
            "y": float(y),
            "width": float(width),
            "height": float(height),
            "strength": float(strength),
        }
        entries.append(entry)
        return (entries,)


class ConditioningPipelineCombine:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "global_positive": ("CONDITIONING",),
                "global_negative": ("CONDITIONING",),
                "pipeline": ("CONDITIONING_PIPELINE",),
            },
            "optional": {
                "global_strength": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 10.0, "step": 0.05}),
            },
        }

    NODE_ID = "ConditioningPipelineCombine"
    NODE_NAME = "Conditioning Pipeline (Combine)"
    CATEGORY = "LoRA Pipeline/Conditioning"
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "CONDITIONING_AREAS")
    RETURN_NAMES = ("positive_out", "negative_out", "areas_out")
    FUNCTION = "run"

    BASE_RES = 64

    @staticmethod
    def _make_fast_mask(x, y, width, height, res):
        mask = torch.zeros(res, res)
        x_start = max(0, min(res, math.floor(x * res)))
        y_start = max(0, min(res, math.floor(y * res)))
        x_end = max(x_start, min(res, math.ceil((x + width) * res)))
        y_end = max(y_start, min(res, math.ceil((y + height) * res)))
        mask[y_start:y_end, x_start:x_end] = 1.0
        return mask.unsqueeze(0)

    @staticmethod
    def _concat_global(conditioning, global_positive, global_strength):
        if global_strength <= 0.0 or not conditioning or not global_positive:
            return conditioning

        global_tokens = global_positive[0][0] * global_strength
        combined = []
        for entry in conditioning:
            tokens = torch.cat((entry[0], global_tokens), dim=1)
            combined.append([tokens, entry[1].copy()])
        return combined

    @staticmethod
    def _masks_cover_canvas(masks):
        if not masks:
            return False
        coverage = torch.zeros_like(masks[0], dtype=torch.bool)
        for mask in masks:
            coverage |= mask > 0
        return bool(torch.all(coverage).item())

    def run(
        self,
        global_positive,
        global_negative,
        pipeline,
        global_strength=0.3,
    ):
        from comfy_execution.graph_utils import GraphBuilder

        global_strength = round(float(global_strength), 2)

        entries = list(pipeline) if pipeline is not None else []

        # Filter valid entries
        valid = []
        for item in entries:
            cond = item.get("conditioning")
            if cond is not None:
                valid.append(item)

        areas_list = [
            {
                "x": float(item["x"]),
                "y": float(item["y"]),
                "width": float(item["width"]),
                "height": float(item["height"]),
                "strength": float(item.get("strength", 1.0)),
            }
            for item in valid
        ]

        if not valid:
            return (global_positive, global_negative, [])

        graph = GraphBuilder()

        masks = []
        acc_pos = None

        for item in valid:
            mask = self._make_fast_mask(
                item["x"], item["y"], item["width"], item["height"], self.BASE_RES,
            )
            masks.append(mask)
            regional_positive = self._concat_global(
                item["conditioning"], global_positive, global_strength,
            )

            if acc_pos is None:
                acc = graph.node(
                    "ConditioningSetProperties",
                    cond_NEW=regional_positive,
                    strength=item.get("strength", 1.0),
                    set_cond_area="default",
                    mask=mask,
                )
            else:
                acc = graph.node(
                    "ConditioningSetPropertiesAndCombine",
                    cond=acc_pos,
                    cond_NEW=regional_positive,
                    strength=item.get("strength", 1.0),
                    set_cond_area="default",
                    mask=mask,
                )
            acc_pos = acc.out(0)

        if not self._masks_cover_canvas(masks):
            fallback = graph.node(
                "ConditioningSetDefaultCombine",
                cond=acc_pos,
                cond_DEFAULT=global_positive,
            )
            acc_pos = fallback.out(0)

        return {
            "result": (acc_pos, global_negative, areas_list),
            "expand": graph.finalize(),
        }


class ConditioningPipelineCombineV2(ConditioningPipelineCombine):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "global_positive": ("CONDITIONING",),
                "global_negative": ("CONDITIONING",),
                "pipeline": ("CONDITIONING_PIPELINE",),
            },
        }

    NODE_ID = "ConditioningPipelineCombineV2"
    NODE_NAME = "Conditioning Pipeline Combine V2"

    def _prepare_regional_conditioning(self, conditioning, global_positive):
        return self._concat_global(conditioning, global_positive, 1.0)

    def run(
        self,
        global_positive,
        global_negative,
        pipeline,
    ):
        from comfy_execution.graph_utils import GraphBuilder

        entries = list(pipeline) if pipeline is not None else []

        valid = []
        for item in entries:
            cond = item.get("conditioning")
            if cond is not None:
                valid.append(item)

        areas_list = [
            {
                "x": float(item["x"]),
                "y": float(item["y"]),
                "width": float(item["width"]),
                "height": float(item["height"]),
                "strength": float(item.get("strength", 1.0)),
            }
            for item in valid
        ]

        if not valid:
            return (global_positive, global_negative, [])

        graph = GraphBuilder()
        acc_pos = None

        for item in valid:
            mask = self._make_fast_mask(
                item["x"], item["y"], item["width"], item["height"], self.BASE_RES,
            )
            regional_positive = self._prepare_regional_conditioning(
                item["conditioning"], global_positive,
            )

            if acc_pos is None:
                acc = graph.node(
                    "ConditioningSetProperties",
                    cond_NEW=regional_positive,
                    strength=item.get("strength", 1.0),
                    set_cond_area="default",
                    mask=mask,
                )
            else:
                acc = graph.node(
                    "ConditioningSetPropertiesAndCombine",
                    cond=acc_pos,
                    cond_NEW=regional_positive,
                    strength=item.get("strength", 1.0),
                    set_cond_area="default",
                    mask=mask,
                )
            acc_pos = acc.out(0)

        fallback = graph.node(
            "ConditioningSetDefaultCombine",
            cond=acc_pos,
            cond_DEFAULT=global_positive,
        )
        acc_pos = fallback.out(0)

        return {
            "result": (acc_pos, global_negative, areas_list),
            "expand": graph.finalize(),
        }
