import base64
import io
import json
import re
from PIL import Image

MAX_IMAGE_SIZE = 1024


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def bytes_to_image(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def resize_image(image: Image.Image, max_size: int = MAX_IMAGE_SIZE) -> Image.Image:
    width, height = image.size
    if width <= max_size and height <= max_size:
        return image

    if width > height:
        new_width = max_size
        new_height = int(height * max_size / width)
    else:
        new_height = max_size
        new_width = int(width * max_size / height)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def parse_layout_string(layout_str: str) -> list[tuple[list[int], str, list[str]]]:
    if not layout_str or not layout_str.strip().startswith("["):
        return []

    results = []
    pattern = r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\],\s*([a-z_]+)(?:,\s*\[(.*?)\])?'

    for match in re.finditer(pattern, layout_str):
        bbox = [int(match.group(i)) for i in range(1, 5)]
        label = match.group(5)
        tags_str = match.group(6)
        tags = [t.strip() for t in tags_str.split(",")] if tags_str else []
        results.append((bbox, label, tags))

    return results


def process_coordinates(bbox: list[int], image: Image.Image, reference_size: int = 1000) -> tuple[int, int, int, int]:
    width, height = image.size
    scale_x = width / reference_size
    scale_y = height / reference_size

    x1 = int(bbox[0] * scale_x)
    y1 = int(bbox[1] * scale_y)
    x2 = int(bbox[2] * scale_x)
    y2 = int(bbox[3] * scale_y)

    x1 = max(0, min(x1, width))
    y1 = max(0, min(y1, height))
    x2 = max(0, min(x2, width))
    y2 = max(0, min(y2, height))

    return x1, y1, x2, y2


def elements_to_markdown(elements: list[dict]) -> str:
    sorted_elements = sorted(elements, key=lambda x: x.get("reading_order", 0))
    parts = []

    for elem in sorted_elements:
        text = elem.get("text", "").strip()
        if not text:
            continue

        label = elem.get("label", "")

        if label == "equ":
            if not text.startswith("$"):
                text = f"$$\n{text}\n$$"
            parts.append(text)
        elif label == "code":
            if not text.startswith("```"):
                text = f"```\n{text}\n```"
            parts.append(text)
        elif label == "tab":
            parts.append(text)
        elif label == "fig":
            parts.append(text)
        else:
            parts.append(text)

    return "\n\n".join(parts)


def elements_to_html(elements: list[dict]) -> str:
    sorted_elements = sorted(elements, key=lambda x: x.get("reading_order", 0))
    parts = ["<div class='document'>"]

    for elem in sorted_elements:
        text = elem.get("text", "").strip()
        if not text:
            continue

        label = elem.get("label", "")
        bbox = elem.get("bbox", [])

        bbox_attr = f"data-bbox='{json.dumps(bbox)}'" if bbox else ""

        if label == "equ":
            parts.append(f"<div class='equation' {bbox_attr}>{text}</div>")
        elif label == "code":
            parts.append(f"<pre class='code' {bbox_attr}><code>{text}</code></pre>")
        elif label == "tab":
            parts.append(f"<div class='table' {bbox_attr}>{text}</div>")
        elif label == "fig":
            parts.append(f"<figure {bbox_attr}>{text}</figure>")
        elif label == "title":
            parts.append(f"<h1 {bbox_attr}>{text}</h1>")
        else:
            parts.append(f"<p {bbox_attr}>{text}</p>")

    parts.append("</div>")
    return "\n".join(parts)


def elements_to_json(elements: list[dict]) -> str:
    sorted_elements = sorted(elements, key=lambda x: x.get("reading_order", 0))
    output = {"elements": sorted_elements}
    return json.dumps(output, ensure_ascii=False, indent=2)
