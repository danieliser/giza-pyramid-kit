#!/usr/bin/env python3
"""Build a maker-site release bundle for the Giza pyramid STL kit."""

from __future__ import annotations

import math
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generate_giza_kit import (
    KitParams,
    Mesh,
    make_capstone,
    make_casing_ring,
    make_cut_temporary_backfill,
    make_display_core_below_capstone,
    make_finished_pyramid_surface,
    make_platform,
    make_ramp_underfill,
    make_ramps,
)

DIST = ROOT / "dist"
RELEASE = ROOT / "release" / "thingiverse"
BUNDLE_NAME = "giza-pyramid-construction-theory-stl-kit"
BUNDLE = RELEASE / "upload_bundle" / BUNDLE_NAME
ZIP_PATH = RELEASE / f"{BUNDLE_NAME}-v0.1.0.zip"
IMAGES = RELEASE / "images"

COPY_DIRS = [
    (DIST / "printable", BUNDLE / "STL" / "printable"),
    (DIST / "constructed_states", BUNDLE / "STL" / "constructed_states"),
    (DIST / "view_stages", BUNDLE / "STL" / "view_stages"),
]

COPY_FILES = [
    (ROOT / "README.md", BUNDLE / "README_GITHUB_PROJECT.md"),
    (ROOT / "docs" / "PRINTING.md", BUNDLE / "PRINTING.md"),
    (ROOT / "dist" / "manifest.json", BUNDLE / "manifest.json"),
    (RELEASE / "LISTING.md", BUNDLE / "THINGIVERSE_LISTING.md"),
    (RELEASE / "UPLOAD_CHECKLIST.md", BUNDLE / "UPLOAD_CHECKLIST.md"),
    (RELEASE / "LICENSE_NOTE.md", BUNDLE / "LICENSE_NOTE.md"),
]


Vec3 = tuple[float, float, float]
Triangle = tuple[Vec3, Vec3, Vec3]
Rgb = tuple[int, int, int]
RenderPart = tuple[Mesh, Rgb]


COLORS: dict[str, Rgb] = {
    "fill": (196, 158, 86),
    "underfill": (147, 124, 76),
    "ramps": (173, 117, 55),
    "platform": (219, 190, 124),
    "capstone": (231, 184, 57),
    "core": (168, 137, 88),
    "casing": (226, 210, 169),
    "finished": (213, 191, 135),
}


def project(point: Vec3) -> Vec3:
    x, y, z = point
    screen_x = (x - y) * 0.8660254
    screen_y = (x + y) * 0.42 - z * 1.12
    depth = x + y + z * 1.2
    return (screen_x, screen_y, depth)


def normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    ux, uy, uz = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    vx, vy, vz = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    mag = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / mag, ny / mag, nz / mag)


def shade_color(base: Rgb, tri: Triangle, light: Vec3) -> Rgb:
    n = normal(*tri)
    facing = abs(sum(n[i] * light[i] for i in range(3)))
    cx = sum(point[0] for point in tri) / 3.0
    cy = sum(point[1] for point in tri) / 3.0
    cz = sum(point[2] for point in tri) / 3.0
    grain = 0.94 + 0.06 * (0.5 + 0.5 * math.sin(cx * 0.19 + cy * 0.13 + cz * 0.31))
    intensity = (0.56 + 0.44 * facing) * grain
    return tuple(max(0, min(255, int(channel * intensity))) for channel in base)


def build_render_scenes() -> list[tuple[str, list[RenderPart]]]:
    params = KitParams()
    cut_backfill = make_cut_temporary_backfill(params)
    ramp_underfill, _ = make_ramp_underfill(params)
    ramps_all, _, _ = make_ramps(params)
    platform = make_platform(params)
    capstone = make_capstone(params)
    finished = make_finished_pyramid_surface(params)

    top_threshold = params.core_height_mm * 0.62
    top_backfill = make_cut_temporary_backfill(params, max_z=top_threshold)
    top_underfill, _ = make_ramp_underfill(params, max_z=top_threshold)
    top_ramps, _, _ = make_ramps(params, max_z=top_threshold)
    display_core = make_display_core_below_capstone(params)
    display_casing = [make_casing_ring(params, i, include_caps=False) for i in range(params.casing_rings)]
    upper_casing = [ring for i, ring in enumerate(display_casing) if (i / params.casing_rings) >= 0.62]

    return [
        (
            "cover_full_ramp_system.png",
            [
                (cut_backfill, COLORS["fill"]),
                (ramp_underfill, COLORS["underfill"]),
                (ramps_all, COLORS["ramps"]),
            ],
        ),
        (
            "capstone_before_deramping.png",
            [
                (cut_backfill, COLORS["fill"]),
                (ramp_underfill, COLORS["underfill"]),
                (ramps_all, COLORS["ramps"]),
                (platform, COLORS["platform"]),
                (capstone, COLORS["capstone"]),
            ],
        ),
        (
            "partial_top_down_deramping.png",
            [
                (display_core, COLORS["core"]),
                (top_backfill, COLORS["fill"]),
                (top_underfill, COLORS["underfill"]),
                (top_ramps, COLORS["ramps"]),
                *[(ring, COLORS["casing"]) for ring in upper_casing],
                (capstone, COLORS["capstone"]),
            ],
        ),
        (
            "finished_pyramid.png",
            [
                (finished, COLORS["finished"]),
            ],
        ),
    ]


def render_scene(parts: list[RenderPart], out_path: Path, size: tuple[int, int] = (1600, 1000)) -> None:
    try:
        import numpy as np
        from PIL import Image
    except Exception as exc:  # pragma: no cover - optional release nicety
        print(f"Skipping renders; Pillow is unavailable: {exc}")
        return

    projected: list[tuple[Triangle, list[Vec3], Rgb, float]] = []
    xs: list[float] = []
    ys: list[float] = []
    for part_order, (mesh, base_color) in enumerate(parts):
        depth_bias = part_order * 0.01
        for tri in mesh.triangles:
            transformed = [project(point) for point in tri]
            projected.append((tri, transformed, base_color, depth_bias))
            xs.extend(point[0] for point in transformed)
            ys.extend(point[1] for point in transformed)

    if not projected:
        return

    width, height = size
    pad = 80
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    scale = min((width - pad * 2) / (max_x - min_x), (height - pad * 2) / (max_y - min_y))
    light = (-0.35, -0.55, 1.0)
    light_mag = math.sqrt(sum(v * v for v in light)) or 1.0
    light = tuple(v / light_mag for v in light)  # type: ignore[assignment]

    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, :] = (246, 240, 223)
    image[height - 165 :, :] = (234, 217, 184)
    zbuffer = np.full((height, width), -np.inf, dtype=np.float32)

    def screen(point: Vec3) -> tuple[float, float]:
        return (
            pad + (point[0] - min_x) * scale,
            pad + (point[1] - min_y) * scale,
        )

    for original, transformed, base_color, depth_bias in projected:
        points = [screen(point) for point in transformed]
        depths = [point[2] + depth_bias for point in transformed]
        x0, y0 = points[0]
        x1, y1 = points[1]
        x2, y2 = points[2]
        min_px = max(0, int(math.floor(min(x0, x1, x2))))
        max_px = min(width - 1, int(math.ceil(max(x0, x1, x2))))
        min_py = max(0, int(math.floor(min(y0, y1, y2))))
        max_py = min(height - 1, int(math.ceil(max(y0, y1, y2))))
        if min_px > max_px or min_py > max_py:
            continue

        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denom) <= 0.000001:
            continue

        yy, xx = np.mgrid[min_py : max_py + 1, min_px : max_px + 1]
        w0 = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / denom
        w1 = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / denom
        w2 = 1.0 - w0 - w1
        mask = (w0 >= -0.0001) & (w1 >= -0.0001) & (w2 >= -0.0001)
        if not mask.any():
            continue

        depth = w0 * depths[0] + w1 * depths[1] + w2 * depths[2]
        z_slice = zbuffer[min_py : max_py + 1, min_px : max_px + 1]
        update = mask & (depth > z_slice)
        if not update.any():
            continue

        z_slice[update] = depth[update]
        image_slice = image[min_py : max_py + 1, min_px : max_px + 1]
        image_slice[update] = shade_color(base_color, original, light)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(out_path)


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(BUNDLE.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(BUNDLE.parent))


def main() -> None:
    required = [src for src, _ in COPY_DIRS] + [src for src, _ in COPY_FILES]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing release inputs:\n" + "\n".join(f"- {path}" for path in missing))

    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    BUNDLE.mkdir(parents=True)
    IMAGES.mkdir(parents=True, exist_ok=True)

    for name, parts in build_render_scenes():
        render_scene(parts, IMAGES / name)

    for src, dst in COPY_DIRS:
        copy_tree(src, dst)
    for src, dst in COPY_FILES:
        copy_file(src, dst)
    copy_tree(IMAGES, BUNDLE / "images")

    build_zip()
    print(f"Release bundle: {BUNDLE}")
    print(f"Upload zip: {ZIP_PATH}")


if __name__ == "__main__":
    main()
