import numpy as np
import torch


# Palette: distinct colors readable on dark and light backgrounds
_AREA_COLORS = [
    (41, 121, 255),   # Blue
    (255, 140, 0),    # Orange
    (0, 200, 80),     # Green
    (220, 50, 220),   # Magenta
    (0, 200, 230),    # Cyan
    (210, 180, 0),    # Gold
]

# Grid visual constants (match the OpenPose Studio canvas style)
_GRID_SPACING = 64
_BG_COLOR = (26, 26, 26)        # #1a1a1a
_GRID_COLOR = (220, 220, 220)   # light gray
_GRID_ALPHA = 0.50
_AXIS_X_COLOR = (0, 255, 0)     # green
_AXIS_Y_COLOR = (255, 0, 0)     # red
_AXIS_ALPHA = 0.30
_BORDER_COLOR = (160, 160, 160)
_BORDER_ALPHA = 0.70

_FILL_ALPHA = 0.18
_BORDER_LINE_ALPHA = 0.85
_LABEL_BG_ALPHA = 0.68
_LABEL_TEXT_ALPHA = 0.92

_MIN_DIM_FOR_FULL_LABEL = 80
_FONT_SIZE = 11
_PAD_H = 4
_PAD_V = 2
_LABEL_INSET = 6
_BORDER_RADIUS = 3


def _load_font(size):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _alpha_blend(base_rgba, overlay_rgba):
    """Blend overlay onto base; both (R,G,B,A) tuples with A in 0-255."""
    ba = base_rgba[3] / 255.0
    oa = overlay_rgba[3] / 255.0
    out_a = oa + ba * (1.0 - oa)
    if out_a < 1e-6:
        return (0, 0, 0, 0)
    out_rgb = tuple(
        int((overlay_rgba[i] * oa + base_rgba[i] * ba * (1.0 - oa)) / out_a)
        for i in range(3)
    )
    return out_rgb + (int(out_a * 255),)


def _render_area_preview(areas, width, height):
    from PIL import Image, ImageDraw

    w, h = int(width), int(height)
    if w < 1 or h < 1:
        w, h = 64, 64

    # ---- background ----
    img = Image.new("RGBA", (w, h), _BG_COLOR + (255,))

    # ---- grid ----
    grid_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid_layer)
    ga = int(_GRID_ALPHA * 255)
    cx, cy = w // 2, h // 2

    for x in range(_GRID_SPACING, w, _GRID_SPACING):
        if abs(x - cx) < 1:
            continue
        gd.line([(x, 0), (x, h - 1)], fill=_GRID_COLOR + (ga,), width=1)
    for y in range(_GRID_SPACING, h, _GRID_SPACING):
        if abs(y - cy) < 1:
            continue
        gd.line([(0, y), (w - 1, y)], fill=_GRID_COLOR + (ga,), width=1)

    aa = int(_AXIS_ALPHA * 255)
    gd.line([(cx, 0), (cx, h - 1)], fill=_AXIS_Y_COLOR + (aa,), width=1)
    gd.line([(0, cy), (w - 1, cy)], fill=_AXIS_X_COLOR + (aa,), width=1)

    img = Image.alpha_composite(img, grid_layer)

    # ---- fills ----
    fills_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fills_layer)
    for i, area in enumerate(areas):
        r, g, b = _AREA_COLORS[i % len(_AREA_COLORS)]
        rx = int(area["x"] * w)
        ry = int(area["y"] * h)
        rw = max(1, int(area["width"] * w))
        rh = max(1, int(area["height"] * h))
        fill_a = int(_FILL_ALPHA * 255)
        try:
            fd.rounded_rectangle(
                [rx, ry, rx + rw, ry + rh],
                radius=_BORDER_RADIUS,
                fill=(r, g, b, fill_a),
            )
        except AttributeError:
            fd.rectangle([rx, ry, rx + rw, ry + rh], fill=(r, g, b, fill_a))

    img = Image.alpha_composite(img, fills_layer)

    # ---- borders ----
    borders_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(borders_layer)
    for i, area in enumerate(areas):
        r, g, b = _AREA_COLORS[i % len(_AREA_COLORS)]
        rx = int(area["x"] * w)
        ry = int(area["y"] * h)
        rw = max(1, int(area["width"] * w))
        rh = max(1, int(area["height"] * h))
        border_a = int(_BORDER_LINE_ALPHA * 255)
        try:
            bd.rounded_rectangle(
                [rx, ry, rx + rw, ry + rh],
                radius=_BORDER_RADIUS,
                outline=(r, g, b, border_a),
                width=2,
            )
        except AttributeError:
            bd.rectangle([rx, ry, rx + rw, ry + rh], outline=(r, g, b, border_a), width=2)

    img = Image.alpha_composite(img, borders_layer)

    # ---- labels ----
    labels_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(labels_layer)
    font = _load_font(_FONT_SIZE)

    for i, area in enumerate(areas):
        rx = int(area["x"] * w)
        ry = int(area["y"] * h)
        rw = max(1, int(area["width"] * w))
        rh = max(1, int(area["height"] * h))

        idx = i + 1
        short_label = f"Area {idx}"
        full_label = (
            f"Area {idx} · x={area['x']:.2f} y={area['y']:.2f}"
            f" w={area['width']:.2f} h={area['height']:.2f}"
        )
        label = full_label if (rw >= _MIN_DIM_FOR_FULL_LABEL and rh >= _MIN_DIM_FOR_FULL_LABEL) else short_label

        # Measure text
        try:
            bbox = ld.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            # Pillow < 8.0.0
            text_w, text_h = ld.textsize(label, font=font)  # type: ignore[attr-defined]

        badge_w = text_w + _PAD_H * 2
        badge_h = text_h + _PAD_V * 2
        bx = rx + _LABEL_INSET
        by = ry + _LABEL_INSET

        # Ensure label fits within the rectangle
        if bx + badge_w > rx + rw or by + badge_h > ry + rh:
            label = short_label
            try:
                bbox = ld.textbbox((0, 0), label, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
            except AttributeError:
                text_w, text_h = ld.textsize(label, font=font)  # type: ignore[attr-defined]
            badge_w = text_w + _PAD_H * 2
            badge_h = text_h + _PAD_V * 2

        bg_a = int(_LABEL_BG_ALPHA * 255)
        try:
            ld.rounded_rectangle(
                [bx, by, bx + badge_w, by + badge_h],
                radius=3,
                fill=(0, 0, 0, bg_a),
            )
        except AttributeError:
            ld.rectangle([bx, by, bx + badge_w, by + badge_h], fill=(0, 0, 0, bg_a))

        txt_a = int(_LABEL_TEXT_ALPHA * 255)
        ld.text((bx + _PAD_H, by + _PAD_V), label, font=font, fill=(255, 255, 255, txt_a))

    img = Image.alpha_composite(img, labels_layer)

    # ---- outer border ----
    outer = ImageDraw.Draw(img)
    ob_a = int(_BORDER_ALPHA * 255)
    outer.rectangle([0, 0, w - 1, h - 1], outline=_BORDER_COLOR + (ob_a,), width=1)

    # ---- convert to float32 RGB tensor [1, H, W, 3] ----
    arr = np.array(img.convert("RGB")).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


class ConditioningAreaPreview:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "areas": ("CONDITIONING_AREAS",),
                "width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
            }
        }

    NODE_ID = "ConditioningAreaPreview"
    NODE_NAME = "Conditioning Area Preview"
    CATEGORY = "LoRA Pipeline/Conditioning"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("preview",)
    FUNCTION = "run"

    def run(self, areas, width, height):
        if not isinstance(areas, list) or len(areas) == 0:
            # Return an empty dark canvas
            empty = torch.zeros((1, int(height), int(width), 3), dtype=torch.float32)
            return (empty,)

        tensor = _render_area_preview(areas, width, height)
        return (tensor,)
