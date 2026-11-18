import importlib.util
import sys
import types
import unittest
from pathlib import Path

import torch


_MODULE_PATH = (
    Path(__file__).parents[1] / "nodes" / "masked_area_conditioning_combine.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "lora_pipeline_masked_area_conditioning",
    _MODULE_PATH,
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
MaskedAreaConditioningCombine = _MODULE.MaskedAreaConditioningCombine


class _Output:
    def __init__(self, node_type, index):
        self.node_type = node_type
        self.index = index


class _Node:
    def __init__(self, node_type):
        self.node_type = node_type

    def out(self, index):
        return _Output(self.node_type, index)


class _GraphBuilder:
    instance = None

    def __init__(self):
        self.calls = []
        _GraphBuilder.instance = self

    def node(self, node_type, **inputs):
        self.calls.append((node_type, inputs))
        return _Node(node_type)

    def finalize(self):
        return self.calls


class MaskedAreaConditioningCombineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        graph_utils = types.ModuleType("comfy_execution.graph_utils")
        graph_utils.GraphBuilder = _GraphBuilder
        comfy_execution = types.ModuleType("comfy_execution")
        comfy_execution.graph_utils = graph_utils
        sys.modules["comfy_execution"] = comfy_execution
        sys.modules["comfy_execution.graph_utils"] = graph_utils

    def test_historical_node_contract_is_preserved(self):
        inputs = MaskedAreaConditioningCombine.INPUT_TYPES()

        self.assertEqual(
            list(inputs["required"]),
            ["global_conditioning", "conditioning_1", "mask_1", "area_strength"],
        )
        self.assertEqual(MaskedAreaConditioningCombine.NODE_ID, "MaskedAreaConditioningCombine")
        self.assertEqual(
            MaskedAreaConditioningCombine.CATEGORY,
            "LoRA Pipeline/Conditioning",
        )
        self.assertEqual(
            MaskedAreaConditioningCombine.RETURN_NAMES,
            ("area_conditioning", "chain_debug_opt"),
        )

    def test_connected_components_are_converted_to_normalized_bounds(self):
        mask = torch.zeros((1, 10, 10))
        mask[0, 1:4, 2:6] = 1.0
        mask[0, 7:9, 8:10] = 1.0

        regions = MaskedAreaConditioningCombine()._find_connected_components(mask)

        self.assertEqual(
            regions,
            [
                (0.2, 0.1, 0.4, 0.3),
                (0.8, 0.7, 0.2, 0.2),
            ],
        )

    def test_two_mask_workflow_expands_to_the_fast_mask_graph(self):
        global_conditioning = object()
        conditioning_1 = object()
        conditioning_2 = object()
        style_conditioning = object()
        mask_1 = torch.zeros((1, 10, 10))
        mask_1[0, :, :5] = 1.0
        mask_2 = torch.zeros((1, 10, 10))
        mask_2[0, :, 5:] = 1.0

        result = MaskedAreaConditioningCombine().run(
            global_conditioning,
            conditioning_1,
            mask_1,
            area_strength=0.3,
            max_regions_per_mask=1,
            min_region_area=0.001,
            conditioning_2=conditioning_2,
            mask_2=mask_2,
            style_conditioning=style_conditioning,
        )

        calls = _GraphBuilder.instance.calls
        self.assertEqual(
            [node_type for node_type, _ in calls],
            [
                "ConditioningConcat",
                "ConditioningConcat",
                "ConditioningSetProperties",
                "ConditioningConcat",
                "ConditioningSetPropertiesAndCombine",
            ],
        )
        mask_calls = [
            inputs
            for node_type, inputs in calls
            if node_type in {
                "ConditioningSetProperties",
                "ConditioningSetPropertiesAndCombine",
            }
        ]
        self.assertEqual(
            [call["strength"] for call in mask_calls],
            [0.3, 0.3],
        )
        torch.testing.assert_close(mask_calls[0]["mask"], mask_1)
        torch.testing.assert_close(mask_calls[1]["mask"], mask_2)
        self.assertEqual(
            result["result"][0].node_type,
            "ConditioningSetPropertiesAndCombine",
        )
        self.assertEqual(result["result"][1].node_type, "ConditioningConcat")

    def test_incomplete_coverage_keeps_global_fallback(self):
        mask = torch.zeros((1, 10, 10))
        mask[0, :, :5] = 1.0

        result = MaskedAreaConditioningCombine().run(
            object(),
            object(),
            mask,
        )

        calls = _GraphBuilder.instance.calls
        self.assertEqual(calls[-1][0], "ConditioningSetDefaultCombine")
        self.assertEqual(
            result["result"][0].node_type,
            "ConditioningSetDefaultCombine",
        )

    def test_region_limit_keeps_only_the_largest_components(self):
        mask = torch.zeros((1, 10, 10))
        mask[0, 0:2, 0:2] = 1.0
        mask[0, 5:9, 5:9] = 1.0

        selected = MaskedAreaConditioningCombine()._select_mask_regions(
            mask,
            max_regions_per_mask=1,
        )

        expected = torch.zeros_like(mask)
        expected[0, 5:9, 5:9] = 1.0
        torch.testing.assert_close(selected, expected)


if __name__ == "__main__":
    unittest.main()
