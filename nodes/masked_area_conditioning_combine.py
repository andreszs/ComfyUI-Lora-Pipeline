class MaskedAreaConditioningCombine:
    """
    Regional conditioning using masks instead of manual coordinates.

    Connected components are filtered using the historical region controls, then
    combined into one modern conditioning mask per prompt. Global and style context
    are concatenated into every regional prompt so full-canvas workflows avoid the
    historical extra positive UNet pass.
    """

    @classmethod
    def INPUT_TYPES(cls):
        float_s = {"default": 0.5, "min": 0.0, "max": 10.0, "step": 0.01}

        inputs = {
            "required": {
                "global_conditioning": ("CONDITIONING",),
                "conditioning_1": ("CONDITIONING",),
                "mask_1": ("MASK",),
                "area_strength": ("FLOAT", float_s),
            },
            "optional": {
                "max_regions_per_mask": (
                    "INT",
                    {"default": 10, "min": 1, "max": 50},
                ),
                "min_region_area": (
                    "FLOAT",
                    {"default": 0.001, "min": 0.0, "max": 0.1, "step": 0.001},
                ),
            },
        }

        for i in range(2, 5):
            inputs["optional"][f"conditioning_{i}"] = ("CONDITIONING",)
            inputs["optional"][f"mask_{i}"] = ("MASK",)

        inputs["optional"]["style_conditioning"] = ("CONDITIONING",)

        return inputs

    NODE_ID = "MaskedAreaConditioningCombine"
    NODE_NAME = "Masked Area Conditioning Combine"
    CATEGORY = "LoRA Pipeline/Conditioning"
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("area_conditioning", "chain_debug_opt")
    FUNCTION = "run"

    def _connected_components(self, mask, min_area=0.001):
        """
        Return the binarized source mask, its component labels, and normalized bounds.
        """
        import numpy as np
        from scipy import ndimage

        if len(mask.shape) == 3:
            mask = mask[0]

        binary_mask = (mask > 0.5).detach().cpu().numpy()
        h, w = binary_mask.shape
        structure = np.array(
            [
                [0, 1, 0],
                [1, 1, 1],
                [0, 1, 0],
            ],
            dtype=np.uint8,
        )
        labels, _ = ndimage.label(binary_mask, structure=structure)
        regions = []
        for label, bounds in enumerate(ndimage.find_objects(labels), start=1):
            if bounds is None:
                continue

            y_slice, x_slice = bounds
            norm_x = x_slice.start / w
            norm_y = y_slice.start / h
            norm_width = (x_slice.stop - x_slice.start) / w
            norm_height = (y_slice.stop - y_slice.start) / h
            region_area = norm_width * norm_height

            if region_area >= min_area:
                regions.append(
                    (label, norm_x, norm_y, norm_width, norm_height)
                )

        return mask, labels, regions

    def _find_connected_components(self, mask, min_area=0.001):
        _, _, regions = self._connected_components(mask, min_area)
        return [region[1:] for region in regions]

    def _select_mask_regions(
        self,
        mask,
        max_regions_per_mask=10,
        min_region_area=0.001,
    ):
        import numpy as np
        import torch

        source_mask, labels, regions = self._connected_components(
            mask,
            min_region_area,
        )
        if len(regions) > max_regions_per_mask:
            regions = sorted(
                regions,
                key=lambda region: region[3] * region[4],
                reverse=True,
            )[:max_regions_per_mask]

        if not regions:
            return None

        selected_labels = [region[0] for region in regions]
        selected = np.isin(labels, selected_labels)
        selected_mask = torch.from_numpy(selected).to(
            device=source_mask.device,
            dtype=source_mask.dtype,
        )
        return selected_mask.unsqueeze(0)

    @staticmethod
    def _masks_cover_canvas(masks):
        import torch
        import torch.nn.functional as functional

        if not masks:
            return False

        height, width = masks[0].shape[-2:]
        coverage = torch.zeros(
            (1, height, width),
            dtype=torch.bool,
            device=masks[0].device,
        )
        for mask in masks:
            current = mask
            if current.shape[-2:] != (height, width):
                current = functional.interpolate(
                    current.unsqueeze(1).float(),
                    size=(height, width),
                    mode="nearest",
                ).squeeze(1)
            current = current.to(device=coverage.device)
            coverage |= current > 0

        return bool(torch.all(coverage).item())

    def run(
        self,
        global_conditioning,
        conditioning_1,
        mask_1,
        area_strength=0.5,
        max_regions_per_mask=10,
        min_region_area=0.001,
        conditioning_2=None,
        mask_2=None,
        conditioning_3=None,
        mask_3=None,
        conditioning_4=None,
        mask_4=None,
        style_conditioning=None,
    ):
        """
        Filter connected mask regions and build fast full-canvas conditioning masks.
        """
        from comfy_execution.graph_utils import GraphBuilder

        regional_entries = []

        masks_and_conditionings = [
            (mask_1, conditioning_1),
            (mask_2, conditioning_2),
            (mask_3, conditioning_3),
            (mask_4, conditioning_4),
        ]

        for mask, conditioning in masks_and_conditionings:
            if mask is None or conditioning is None:
                continue

            selected_mask = self._select_mask_regions(
                mask,
                max_regions_per_mask,
                min_region_area,
            )
            if selected_mask is not None:
                regional_entries.append((conditioning, selected_mask))

        if not regional_entries:
            # No valid regions found - return global conditioning only
            return (global_conditioning, global_conditioning)

        graph = GraphBuilder()

        master_context = global_conditioning

        if style_conditioning is not None:
            master_context = graph.node(
                "ConditioningConcat",
                conditioning_to=global_conditioning,
                conditioning_from=style_conditioning,
            ).out(0)

        masks = []
        accumulated = None
        for conditioning, mask in regional_entries:
            regional = graph.node(
                "ConditioningConcat",
                conditioning_to=conditioning,
                conditioning_from=master_context,
            ).out(0)
            masks.append(mask)

            if accumulated is None:
                combined = graph.node(
                    "ConditioningSetProperties",
                    cond_NEW=regional,
                    strength=area_strength,
                    set_cond_area="default",
                    mask=mask,
                )
            else:
                combined = graph.node(
                    "ConditioningSetPropertiesAndCombine",
                    cond=accumulated,
                    cond_NEW=regional,
                    strength=area_strength,
                    set_cond_area="default",
                    mask=mask,
                )
            accumulated = combined.out(0)

        if not self._masks_cover_canvas(masks):
            fallback = graph.node(
                "ConditioningSetDefaultCombine",
                cond=accumulated,
                cond_DEFAULT=master_context,
            )
            accumulated = fallback.out(0)

        return {
            "result": (accumulated, master_context),
            "expand": graph.finalize(),
        }
