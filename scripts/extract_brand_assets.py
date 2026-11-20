"""Extract the brand book's bundled SVG marks and WOFF2 font subsets."""

from __future__ import annotations

import argparse
import base64
import binascii
import copy
import gzip
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRAND_BOOK = ROOT / "brand" / "QUANTUM Psychology — Brend kitobi.html"
ASSET_DIR = ROOT / "webapp" / "assets"
FONT_DIR = ROOT / "webapp" / "fonts"
FONT_CSS = ROOT / "webapp" / "fonts.css"
SVG_NS = "http://www.w3.org/2000/svg"
WOFF2_MAGIC = b"wOF2"
VIEW_BOX_PARTS = 4
VIEW_BOX_WIDTH_INDEX = 2
VIEW_BOX_HEIGHT_INDEX = 3
MARK_ELLIPSE_COUNT = 3
MARK_ELLIPSE_RX = "44"
MARK_ELLIPSE_RY = "15"
MAIN_MARK_WIDTH = "150"
LIGHT_MARK_STROKE = "#9C7A35"
APP_MARK_WIDTH = 76
APP_ICON_SIZE = 112
APP_ICON_RADIUS = 28
APP_MARK_OFFSET = (APP_ICON_SIZE - APP_MARK_WIDTH) // 2
PERCENT_SCALE = 100
EXPECTED_WEIGHTS = {
    ("Cormorant Garamond", "normal"): {500, 600, 700},
    ("Cormorant Garamond", "italic"): {500, 600},
    ("Montserrat", "normal"): {400, 500, 600, 700, 800},
}
SUBSET_PREFIXES = {
    "U+0460-052F": "cyrillic-ext",
    "U+0301": "cyrillic",
    "U+0000-00FF": "latin",
}
SCRIPT_RE = re.compile(
    r"<script\b(?=[^>]*\btype=[\"'](?P<type>__bundler/(?:manifest|template))[\"'])"
    r"[^>]*>(?P<body>.*?)</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
SVG_RE = re.compile(r"<svg\b[^>]*>.*?</svg\s*>", re.IGNORECASE | re.DOTALL)
FONT_FACE_RE = re.compile(r"@font-face\s*\{([^{}]*)\}", re.IGNORECASE | re.DOTALL)
CSS_URL_RE = re.compile(r"url\(\s*([^)]*?)\s*\)", re.IGNORECASE)
ET.register_namespace("", SVG_NS)


class AssetError(Exception):
    """A source or extracted asset failed validation."""


@dataclass
class FontSource:
    family: str
    style: str
    subset: str
    unicode_range: str
    resource_id: str
    data: bytes
    weights: set[int] = field(default_factory=set)

    @property
    def filename(self) -> str:
        stem = self.family.lower().replace(" ", "-")
        weight_label = "-".join(str(weight) for weight in (min(self.weights), max(self.weights)))
        style_label = "-italic" if self.style == "italic" else ""
        return f"{stem}-{weight_label}{style_label}-{self.subset}.woff2"


def bundled_script(html: str, script_type: str, context: str) -> str:
    for match in SCRIPT_RE.finditer(html):
        if match.group("type").lower() == f"__bundler/{script_type}":
            return match.group("body").strip()
    raise AssetError(f"{context}: missing __bundler/{script_type} script")


def manifest_from(html: str, context: str) -> dict:
    manifest = json.loads(bundled_script(html, "manifest", context))
    if not isinstance(manifest, dict):
        raise AssetError(f"{context}: manifest must be a JSON object")
    for resource_id, resource in manifest.items():
        if not isinstance(resource, dict):
            raise AssetError(f"{context}: resource {resource_id}: expected an object")
        if not isinstance(resource.get("mime"), str) or not isinstance(resource.get("data"), str):
            raise AssetError(f"{context}: resource {resource_id}: missing or invalid mime/data")
    return manifest


def decode_resource(resource: dict, context: str) -> bytes:
    if not isinstance(resource, dict) or not isinstance(resource.get("data"), str):
        raise AssetError(f"{context}: missing base64 data")
    try:
        data = base64.b64decode(resource["data"], validate=True)
        return gzip.decompress(data) if resource.get("compressed") else data
    except (binascii.Error, ValueError, OSError, EOFError, zlib.error) as exc:
        raise AssetError(f"{context}: cannot decode bundle: {exc}") from exc


def logo_page() -> tuple[str, dict]:
    outer_html = BRAND_BOOK.read_text(encoding="utf-8")
    outer_manifest = manifest_from(outer_html, "brand book")
    for resource_id, resource in outer_manifest.items():
        if resource.get("mime") != "text/html":
            continue
        page = decode_resource(resource, f"page {resource_id}").decode("utf-8")
        if re.search(r"<title>\s*01 Logo\s*</title>", page, re.IGNORECASE):
            inner_manifest = manifest_from(page, "01 Logo page")
            template = json.loads(bundled_script(page, "template", "01 Logo page"))
            if not isinstance(template, str):
                raise AssetError("01 Logo page: template must be HTML text")
            return template, inner_manifest
    raise AssetError("brand book: 01 Logo page was not found")


def validate_svg(data: bytes, filename: str) -> ET.Element:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise AssetError(f"{filename}: invalid SVG XML: {exc}") from exc
    if root.tag != f"{{{SVG_NS}}}svg":
        raise AssetError(f"{filename}: root SVG namespace is missing")
    view_box = root.get("viewBox")
    if not view_box:
        raise AssetError(f"{filename}: viewBox is missing")
    try:
        parts = [float(value) for value in view_box.replace(",", " ").split()]
    except ValueError as exc:
        raise AssetError(f"{filename}: invalid viewBox: {view_box}") from exc
    if (len(parts) != VIEW_BOX_PARTS or not all(math.isfinite(part) for part in parts)
            or parts[VIEW_BOX_WIDTH_INDEX] <= 0 or parts[VIEW_BOX_HEIGHT_INDEX] <= 0):
        raise AssetError(f"{filename}: invalid viewBox: {view_box}")
    local_ids = {node.get("id") for node in root.iter() if node.get("id")}
    for node in root.iter():
        local_name = node.tag.rsplit("}", 1)[-1].lower()
        if local_name in {"script", "foreignobject", "style"}:
            raise AssetError(f"{filename}: forbidden SVG element: {local_name}")
        for name, value in node.attrib.items():
            attribute = name.rsplit("}", 1)[-1].lower()
            if "sc-camel" in attribute or attribute.startswith("on"):
                raise AssetError(f"{filename}: forbidden SVG attribute: {name}")
            if attribute == "href" and (not value.startswith("#") or value[1:] not in local_ids):
                raise AssetError(f"{filename}: external SVG reference: {value}")
            for match in CSS_URL_RE.finditer(value):
                target = match.group(1).strip("\"' ")
                if not target.startswith("#") or target[1:] not in local_ids:
                    raise AssetError(f"{filename}: external SVG URL: {target}")
    return root


def normalize_svg(markup: str, filename: str) -> tuple[bytes, ET.Element]:
    markup = markup.replace("sc-camel-view-box", "viewBox")
    markup = re.sub(r"<svg\b", f'<svg xmlns="{SVG_NS}"', markup, count=1, flags=re.IGNORECASE)
    data = (markup + "\n").encode("utf-8")
    return data, validate_svg(data, filename)


def is_atom(root: ET.Element) -> bool:
    ellipses = root.findall(f".//{{{SVG_NS}}}ellipse")
    return len(ellipses) == MARK_ELLIPSE_COUNT and all(
        ellipse.get("rx") == MARK_ELLIPSE_RX and ellipse.get("ry") == MARK_ELLIPSE_RY
        for ellipse in ellipses
    )


def build_app_icon(source: ET.Element, wrapper: str) -> bytes:
    pattern = re.compile(
        rf"width:\s*{APP_ICON_SIZE}px;\s*height:\s*{APP_ICON_SIZE}px;\s*"
        rf"border-radius:\s*{APP_ICON_RADIUS}px;\s*background:\s*"
        r"radial-gradient\(circle at (\d+)% (\d+)%,\s*(#[0-9a-fA-F]{6}),\s*"
        r"(#[0-9a-fA-F]{6}) (\d+)%\)"
    )
    match = pattern.search(wrapper)
    if not match:
        raise AssetError("01 Logo page: 112px rounded app icon wrapper was not found")
    center_x, center_y, center_color, edge_color, edge_stop = match.groups()
    cx = APP_ICON_SIZE * int(center_x) / PERCENT_SCALE
    cy = APP_ICON_SIZE * int(center_y) / PERCENT_SCALE
    radius = math.hypot(max(cx, APP_ICON_SIZE - cx), max(cy, APP_ICON_SIZE - cy))
    icon = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": str(APP_ICON_SIZE), "height": str(APP_ICON_SIZE),
        "viewBox": f"0 0 {APP_ICON_SIZE} {APP_ICON_SIZE}",
    })
    definitions = ET.SubElement(icon, f"{{{SVG_NS}}}defs")
    gradient = ET.SubElement(definitions, f"{{{SVG_NS}}}radialGradient", {
        "id": "icon-background", "gradientUnits": "userSpaceOnUse",
        "cx": str(cx), "cy": str(cy), "r": str(radius),
    })
    ET.SubElement(gradient, f"{{{SVG_NS}}}stop", {"offset": "0%", "stop-color": center_color})
    ET.SubElement(gradient, f"{{{SVG_NS}}}stop", {"offset": f"{edge_stop}%", "stop-color": edge_color})
    ET.SubElement(icon, f"{{{SVG_NS}}}rect", {
        "width": str(APP_ICON_SIZE), "height": str(APP_ICON_SIZE),
        "rx": str(APP_ICON_RADIUS), "fill": "url(#icon-background)",
    })
    nested = ET.SubElement(icon, f"{{{SVG_NS}}}svg", {
        "x": str(APP_MARK_OFFSET), "y": str(APP_MARK_OFFSET),
        "width": str(APP_MARK_WIDTH), "height": str(APP_MARK_WIDTH),
        "viewBox": source.get("viewBox", ""), "fill": source.get("fill", "none"),
    })
    for child in source:
        nested.append(copy.deepcopy(child))
    data = ET.tostring(icon, encoding="utf-8", xml_declaration=False) + b"\n"
    validate_svg(data, "app-icon.svg")
    return data


def extract_svgs(template: str) -> dict[str, bytes]:
    assets: dict[str, bytes] = {}
    for match in SVG_RE.finditer(template):
        data, root = normalize_svg(match.group(), "01 Logo page SVG")
        if not is_atom(root):
            continue
        stroke_colors = {node.get("stroke") for node in root.iter() if node.get("stroke")}
        if root.get("width") == MAIN_MARK_WIDTH and "#D4AF6A" in stroke_colors:
            assets["logo-mark.svg"] = data
        elif LIGHT_MARK_STROKE in stroke_colors:
            assets["logo-mark-light.svg"] = data
        elif root.get("width") == str(APP_MARK_WIDTH) and "#D4AF6A" in stroke_colors:
            wrapper_start = template.rfind("<div style=", 0, match.start())
            wrapper = template[wrapper_start:match.start()] if wrapper_start >= 0 else ""
            assets["app-icon.svg"] = build_app_icon(root, wrapper)
    expected = {"logo-mark.svg", "logo-mark-light.svg", "app-icon.svg"}
    if set(assets) != expected:
        raise AssetError(f"01 Logo page: missing SVG variants: {', '.join(sorted(expected - set(assets)))}")
    return assets


def css_property(block: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*:\s*([^;]+);", block, re.IGNORECASE)
    if not match:
        raise AssetError(f"01 Logo page: @font-face is missing {name}")
    return match.group(1).strip().strip("\"'")


def extract_fonts(template: str, manifest: dict) -> list[FontSource]:
    fonts: dict[tuple[str, str, str, str], FontSource] = {}
    for face_match in FONT_FACE_RE.finditer(template):
        block = face_match.group(1)
        family = css_property(block, "font-family")
        style = css_property(block, "font-style")
        if (family, style) not in EXPECTED_WEIGHTS:
            continue
        source = css_property(block, "src")
        url_match = CSS_URL_RE.search(source)
        if not url_match:
            raise AssetError(f"{family} {style}: @font-face has no URL")
        resource_id = url_match.group(1).strip("\"' ")
        if resource_id not in manifest:
            continue  # Source CSS also names remote-only subsets, which cannot be extracted offline.
        unicode_range = css_property(block, "unicode-range")
        subset = next((name for prefix, name in SUBSET_PREFIXES.items()
                       if unicode_range.startswith(prefix)), None)
        if subset is None:
            raise AssetError(f"{family} {style}: unknown embedded subset: {unicode_range}")
        resource = manifest[resource_id]
        if resource.get("mime") != "font/woff2":
            raise AssetError(f"{family} {style} {subset}: resource is not WOFF2")
        key = (family, style, subset, resource_id)
        if key not in fonts:
            data = decode_resource(resource, f"{family} {style} {subset}")
            if not data.startswith(WOFF2_MAGIC):
                raise AssetError(f"{family} {style} {subset}: invalid WOFF2 magic")
            fonts[key] = FontSource(family, style, subset, unicode_range, resource_id, data)
        weight_text = css_property(block, "font-weight")
        try:
            fonts[key].weights.add(int(weight_text))
        except ValueError as exc:
            raise AssetError(f"{family} {style} {subset}: invalid font weight: {weight_text}") from exc
    for family_style, expected_weights in EXPECTED_WEIGHTS.items():
        for subset in SUBSET_PREFIXES.values():
            matching = [item for item in fonts.values()
                        if (item.family, item.style, item.subset) == (*family_style, subset)]
            weights = set().union(*(item.weights for item in matching))
            if weights != expected_weights:
                raise AssetError(
                    f"01 Logo page: {family_style[0]} {family_style[1]} {subset} "
                    f"weights {sorted(weights)}; expected {sorted(expected_weights)}"
                )
    return sorted(fonts.values(), key=lambda item: (item.family, item.style, item.subset))


def font_css(fonts: list[FontSource]) -> bytes:
    lines = ["/* Extracted from the QUANTUM Psychology brand book. */"]
    for font in fonts:
        weights = sorted(font.weights)
        weight_range = f"{weights[0]} {weights[-1]}" if len(weights) > 1 else str(weights[0])
        lines.extend([
            "@font-face {",
            f"  font-family: '{font.family}';",
            f"  font-style: {font.style};",
            f"  font-weight: {weight_range};",
            "  font-display: swap;",
            f"  src: url('fonts/{font.filename}') format('woff2');",
            f"  unicode-range: {font.unicode_range};",
            "}",
            "",
        ])
    return ("\n".join(lines) + "\n").encode("utf-8")


def verify_assets(svgs: dict[str, bytes], fonts: list[FontSource], css: bytes) -> None:
    for filename, expected in svgs.items():
        path = ASSET_DIR / filename
        if not path.is_file():
            raise AssetError(f"missing SVG: {path.relative_to(ROOT)}")
        actual = path.read_bytes()
        validate_svg(actual, filename)
        if actual != expected:
            raise AssetError(f"{path.relative_to(ROOT)} differs from the brand book extraction")
    for path in ASSET_DIR.glob("*.svg"):
        validate_svg(path.read_bytes(), path.name)
    for font in fonts:
        path = FONT_DIR / font.filename
        if not path.is_file():
            raise AssetError(f"missing font: {path.relative_to(ROOT)}")
        actual = path.read_bytes()
        if not actual.startswith(WOFF2_MAGIC):
            raise AssetError(f"{path.relative_to(ROOT)} has invalid WOFF2 magic")
        if actual != font.data:
            raise AssetError(f"{path.relative_to(ROOT)} differs from the brand book extraction")
    for path in FONT_DIR.glob("*.woff2"):
        if not path.read_bytes().startswith(WOFF2_MAGIC):
            raise AssetError(f"{path.relative_to(ROOT)} has invalid WOFF2 magic")
    if not FONT_CSS.is_file() or FONT_CSS.read_bytes() != css:
        raise AssetError("webapp/fonts.css is missing or differs from the extracted font faces")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate generated assets without writing")
    args = parser.parse_args()
    try:
        template, manifest = logo_page()
        svgs = extract_svgs(template)
        fonts = extract_fonts(template, manifest)
        css = font_css(fonts)
        if args.check:
            verify_assets(svgs, fonts, css)
            print(f"OK: {len(svgs)} SVGs, {len(fonts)} WOFF2 subsets, fonts.css")
        else:
            ASSET_DIR.mkdir(parents=True, exist_ok=True)
            FONT_DIR.mkdir(parents=True, exist_ok=True)
            for filename, data in svgs.items():
                (ASSET_DIR / filename).write_bytes(data)
            for font in fonts:
                (FONT_DIR / font.filename).write_bytes(font.data)
            FONT_CSS.write_bytes(css)
            print(f"Extracted {len(svgs)} SVGs and {len(fonts)} WOFF2 subsets; wrote fonts.css")
        return 0
    except (AssetError, OSError, UnicodeError, json.JSONDecodeError, ET.ParseError) as exc:
        print(f"Brand asset extraction failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
