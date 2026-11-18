# Changelog

## 1.2.0

- Added `Conditioning Pipeline (Combine) V2`, which gives every region the full global positive context without a `global_strength` input, while preserving global negative conditioning and area metadata outputs.
- Added `Masked Area Conditioning Combine` for mask-driven regional conditioning with up to four conditioning/mask pairs, optional style conditioning, connected-component filtering, and fallback for uncovered areas.
- Made the optimized conditioning path permanent in `Conditioning Pipeline (Combine)` and removed `fast_mode` because its disabled legacy path bypassed per-area LoRA conditioning.
- Grouped all nodes under `LoRA Pipeline` and declared SciPy as an installed dependency for mask connected-component filtering.
- Added V2 example workflows and refreshed the README showcases with workflow-enabled PNG examples that can be opened or dragged into ComfyUI.

## 1.1.4

- Optimized regional conditioning reduced measured generation time from about 144 seconds to 70 seconds in a tested two-region SDXL workflow—approximately 51% less render time.
- Added the optional Fast Mode. In an equivalent full-coverage test it completed in about 54 seconds—up to approximately 63% less render time than the previous implementation.
- Performance varies by GPU, model, resolution, sampler, ControlNet setup, and regional coverage. Fast Mode can also produce visual differences, so it remains disabled by default.
