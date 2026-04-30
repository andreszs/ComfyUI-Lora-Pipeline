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
    def _make_mask(x, y, width, height, res):
        mask = torch.zeros(res, res)
        x_px = int(x * res)
        y_px = int(y * res)
        w_px = int(width * res)
        h_px = int(height * res)
        mask[y_px : y_px + h_px, x_px : x_px + w_px] = 1.0
        return mask.unsqueeze(0)

    def run(self, global_positive, global_negative, pipeline, global_strength=0.3):
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

        # First entry: PairConditioningSetProperties (no previous combined state yet)
        first = valid[0]
        mask_0 = self._make_mask(
            first["x"], first["y"], first["width"], first["height"], self.BASE_RES,
        )
        acc = graph.node(
            "PairConditioningSetProperties",
            positive_NEW=first["conditioning"],
            negative_NEW=global_negative,
            strength=first.get("strength", 1.0),
            set_cond_area="default",
            mask=mask_0,
        )
        acc_pos = acc.out(0)
        acc_neg = acc.out(1)

        # Entries siguientes: PairConditioningSetPropertiesAndCombine
        for item in valid[1:]:
            mask_i = self._make_mask(
                item["x"], item["y"], item["width"], item["height"], self.BASE_RES,
            )
            acc = graph.node(
                "PairConditioningSetPropertiesAndCombine",
                positive=acc_pos,
                negative=acc_neg,
                positive_NEW=item["conditioning"],
                negative_NEW=global_negative,
                strength=item.get("strength", 1.0),
                set_cond_area="default",
                mask=mask_i,
            )
            acc_pos = acc.out(0)
            acc_neg = acc.out(1)

        # Global como entrada full-image con strength controlable
        if global_strength > 0.0:
            global_mask = self._make_mask(0.0, 0.0, 1.0, 1.0, self.BASE_RES)
            acc = graph.node(
                "PairConditioningSetPropertiesAndCombine",
                positive=acc_pos,
                negative=acc_neg,
                positive_NEW=global_positive,
                negative_NEW=global_negative,
                strength=global_strength,
                set_cond_area="default",
                mask=global_mask,
            )
            acc_pos = acc.out(0)
            acc_neg = acc.out(1)

        # Default fallback (safety net para pixeles sin cubrir)
        final = graph.node(
            "PairConditioningSetDefaultCombine",
            positive=acc_pos,
            negative=acc_neg,
            positive_DEFAULT=global_positive,
            negative_DEFAULT=global_negative,
        )

        return {
            "result": (final.out(0), final.out(1), areas_list),
            "expand": graph.finalize(),
        }
