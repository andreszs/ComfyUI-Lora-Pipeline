import importlib.util
import sys
import types
import unittest
from pathlib import Path

import torch


_MODULE_PATH = Path(__file__).parents[1] / "nodes" / "cond_area_pipeline.py"
_SPEC = importlib.util.spec_from_file_location("lora_pipeline_cond_area", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
ConditioningPipelineCombine = _MODULE.ConditioningPipelineCombine


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


class ConditioningPipelineCombineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        graph_utils = types.ModuleType("comfy_execution.graph_utils")
        graph_utils.GraphBuilder = _GraphBuilder
        comfy_execution = types.ModuleType("comfy_execution")
        comfy_execution.graph_utils = graph_utils
        sys.modules["comfy_execution"] = comfy_execution
        sys.modules["comfy_execution.graph_utils"] = graph_utils

    def test_negative_conditioning_is_not_duplicated_per_area(self):
        global_positive = object()
        global_negative = object()
        pipeline = [
            {
                "conditioning": object(),
                "x": 0.0,
                "y": 0.0,
                "width": 0.5,
                "height": 1.0,
                "strength": 0.8,
            },
            {
                "conditioning": object(),
                "x": 0.5,
                "y": 0.0,
                "width": 0.5,
                "height": 1.0,
                "strength": 0.8,
            },
        ]

        result = ConditioningPipelineCombine().run(
            global_positive,
            global_negative,
            pipeline,
            global_strength=0.3,
        )

        positive, negative, areas = result["result"]
        calls = _GraphBuilder.instance.calls

        self.assertIs(negative, global_negative)
        self.assertEqual(len(areas), 2)
        self.assertEqual(
            [node_type for node_type, _ in calls],
            [
                "ConditioningSetProperties",
                "ConditioningSetPropertiesAndCombine",
                "ConditioningSetPropertiesAndCombine",
                "ConditioningSetDefaultCombine",
            ],
        )
        self.assertEqual(positive.node_type, "ConditioningSetDefaultCombine")
        self.assertFalse(any(node_type.startswith("PairConditioning") for node_type, _ in calls))

    def test_fast_mode_concatenates_global_positive_and_skips_full_coverage_fallback(self):
        global_positive = [[torch.full((1, 1, 2), 2.0), {}]]
        global_negative = object()
        pipeline = [
            {
                "conditioning": [[torch.full((1, 1, 2), 1.0), {}]],
                "x": 0.0,
                "y": 0.0,
                "width": 0.5,
                "height": 1.0,
                "strength": 0.8,
            },
            {
                "conditioning": [[torch.full((1, 1, 2), 3.0), {}]],
                "x": 0.5,
                "y": 0.0,
                "width": 0.5,
                "height": 1.0,
                "strength": 0.8,
            },
        ]

        result = ConditioningPipelineCombine().run(
            global_positive,
            global_negative,
            pipeline,
            global_strength=0.25,
            fast_mode=True,
        )

        positive, negative, _ = result["result"]
        calls = _GraphBuilder.instance.calls
        first_tokens = calls[0][1]["cond_NEW"][0][0]

        self.assertIs(negative, global_negative)
        self.assertEqual(
            [node_type for node_type, _ in calls],
            [
                "ConditioningSetProperties",
                "ConditioningSetPropertiesAndCombine",
            ],
        )
        self.assertEqual(positive.node_type, "ConditioningSetPropertiesAndCombine")
        self.assertEqual(first_tokens.shape[1], 2)
        torch.testing.assert_close(first_tokens[:, 1:, :], torch.full((1, 1, 2), 0.5))

    def test_fast_mode_keeps_global_fallback_for_incomplete_coverage(self):
        global_positive = [[torch.ones((1, 1, 2)), {}]]
        pipeline = [
            {
                "conditioning": [[torch.ones((1, 1, 2)), {}]],
                "x": 0.0,
                "y": 0.0,
                "width": 0.5,
                "height": 1.0,
                "strength": 1.0,
            },
        ]

        result = ConditioningPipelineCombine().run(
            global_positive,
            object(),
            pipeline,
            fast_mode=True,
        )

        positive = result["result"][0]
        calls = _GraphBuilder.instance.calls

        self.assertEqual(calls[-1][0], "ConditioningSetDefaultCombine")
        self.assertEqual(positive.node_type, "ConditioningSetDefaultCombine")

    def test_fast_mode_overlapping_fractional_regions_cover_canvas(self):
        conditioning = [[torch.ones((1, 1, 2)), {}]]
        pipeline = [
            {
                "conditioning": conditioning,
                "x": 0.0,
                "y": 0.0,
                "width": 0.52,
                "height": 1.0,
                "strength": 1.0,
            },
            {
                "conditioning": conditioning,
                "x": 0.48,
                "y": 0.0,
                "width": 0.52,
                "height": 1.0,
                "strength": 1.0,
            },
        ]

        ConditioningPipelineCombine().run(
            conditioning,
            object(),
            pipeline,
            fast_mode=True,
        )

        calls = _GraphBuilder.instance.calls
        self.assertFalse(
            any(node_type == "ConditioningSetDefaultCombine" for node_type, _ in calls),
        )


if __name__ == "__main__":
    unittest.main()
