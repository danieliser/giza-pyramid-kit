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


def visible_mesh_edges(mesh: Mesh, screen, zbuffer, depth_bias: float, crease_dot: float = 0.72) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    edges: dict[tuple[Vec3, Vec3], list[tuple[Vec3, Vec3, Vec3, Vec3]]] = {}

    def vertex_key(vertex: Vec3) -> Vec3:
        return tuple(round(value, 4) for value in vertex)  # type: ignore[return-value]

    def edge_key(a: Vec3, b: Vec3) -> tuple[Vec3, Vec3]:
        ak = vertex_key(a)
        bk = vertex_key(b)
        return (ak, bk) if ak <= bk else (bk, ak)

    def add_edge(a: Vec3, b: Vec3, tri: Triangle, n: Vec3) -> None:
        edges.setdefault(edge_key(a, b), []).append((a, b, tri[0], n))

    for tri in mesh.triangles:
        n = normal(*tri)
        add_edge(tri[0], tri[1], tri, n)
        add_edge(tri[1], tri[2], tri, n)
        add_edge(tri[2], tri[0], tri, n)

    height, width = zbuffer.shape
    result: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for records in edges.values():
        if len(records) == 1:
            should_draw = True
        elif len(records) == 2:
            n0 = records[0][3]
            n1 = records[1][3]
            dot = sum(n0[i] * n1[i] for i in range(3))
            should_draw = dot < crease_dot
        else:
            should_draw = False
        if not should_draw:
            continue

        a, b = records[0][0], records[0][1]
        midpoint = ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
        sx, sy = screen(project(midpoint))
        px = min(width - 1, max(0, int(round(sx))))
        py = min(height - 1, max(0, int(round(sy))))
        edge_depth = project(midpoint)[2] + depth_bias
        if not math.isfinite(float(zbuffer[py, px])) or edge_depth < float(zbuffer[py, px]) - 1.8:
            continue

        result.append((screen(project(a)), screen(project(b))))
    return result


def render_scene(parts: list[RenderPart], out_path: Path, size: tuple[int, int] = (1600, 1000)) -> None:
    try:
        import numpy as np
        from PIL import Image, ImageDraw, ImageFilter
    except Exception as exc:  # pragma: no cover - optional release nicety
        print(f"Skipping renders; Pillow is unavailable: {exc}")
        return

    projected: list[tuple[Triangle, list[Vec3], Rgb, float]] = []
    xs: list[float] = []
    ys: list[float] = []
    depths: list[float] = []
    world_xs: list[float] = []
    world_ys: list[float] = []
    world_zs: list[float] = []
    for part_order, (mesh, base_color) in enumerate(parts):
        depth_bias = part_order * 0.01
        for tri in mesh.triangles:
            transformed = [project(point) for point in tri]
            projected.append((tri, transformed, base_color, depth_bias))
            xs.extend(point[0] for point in transformed)
            ys.extend(point[1] for point in transformed)
            depths.extend(point[2] for point in transformed)
            world_xs.extend(point[0] for point in tri)
            world_ys.extend(point[1] for point in tri)
            world_zs.extend(point[2] for point in tri)

    if not projected:
        return

    width, height = size
    pad = 80
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_depth, max_depth = min(depths), max(depths)
    min_world_x, max_world_x = min(world_xs), max(world_xs)
    min_world_y, max_world_y = min(world_ys), max(world_ys)
    min_world_z, max_world_z = min(world_zs), max(world_zs)
    depth_range = max(max_depth - min_depth, 0.000001)
    world_x_range = max(max_world_x - min_world_x, 0.000001)
    world_y_range = max(max_world_y - min_world_y, 0.000001)
    world_z_range = max(max_world_z - min_world_z, 0.000001)
    scale = min((width - pad * 2) / (max_x - min_x), (height - pad * 2) / (max_y - min_y))

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
        world_x = w0 * original[0][0] + w1 * original[1][0] + w2 * original[2][0]
        world_y = w0 * original[0][1] + w1 * original[1][1] + w2 * original[2][1]
        world_z = w0 * original[0][2] + w1 * original[1][2] + w2 * original[2][2]
        z_tone = (world_z - min_world_z) / world_z_range
        xy_tone = 0.5 * ((world_x - min_world_x) / world_x_range) + 0.5 * ((world_y - min_world_y) / world_y_range)
        depth_tone = (depth - min_depth) / depth_range
        tone = 0.74 + 0.15 * z_tone + 0.08 * depth_tone + 0.03 * xy_tone
        tone = np.clip(tone, 0.68, 1.03)
        base = np.array(base_color, dtype=np.float32)
        color = np.clip(tone[..., None] * base, 0, 255).astype(np.uint8)
        image_slice = image[min_py : max_py + 1, min_px : max_px + 1]
        image_slice[update] = color[update]

    valid = np.isfinite(zbuffer)
    edge = np.zeros((height, width), dtype=bool)
    edge_threshold = max(depth_range / 260.0, 0.7)
    upper = valid[:-1, :] & valid[1:, :]
    vertical_diff = np.zeros_like(zbuffer[:-1, :])
    vertical_diff[upper] = np.abs(zbuffer[:-1, :][upper] - zbuffer[1:, :][upper])
    vertical_jump = upper & (vertical_diff > edge_threshold)
    edge[:-1, :] |= vertical_jump
    edge[1:, :] |= vertical_jump
    horizontal = valid[:, :-1] & valid[:, 1:]
    horizontal_diff = np.zeros_like(zbuffer[:, :-1])
    horizontal_diff[horizontal] = np.abs(zbuffer[:, :-1][horizontal] - zbuffer[:, 1:][horizontal])
    horizontal_jump = horizontal & (horizontal_diff > edge_threshold)
    edge[:, :-1] |= horizontal_jump
    edge[:, 1:] |= horizontal_jump
    edge[:-1, :] |= valid[:-1, :] & ~valid[1:, :]
    edge[1:, :] |= valid[1:, :] & ~valid[:-1, :]
    edge[:, :-1] |= valid[:, :-1] & ~valid[:, 1:]
    edge[:, 1:] |= valid[:, 1:] & ~valid[:, :-1]
    image[edge] = (image[edge].astype(np.float32) * 0.83).astype(np.uint8)

    model_mask = Image.fromarray((valid * 255).astype(np.uint8), mode="L")
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow_alpha = model_mask.filter(ImageFilter.GaussianBlur(12))
    shadow_alpha = shadow_alpha.point(lambda value: int(value * 0.18))
    shadow.paste((88, 62, 28, 255), (26, 24), shadow_alpha)

    model_image = Image.fromarray(image).filter(ImageFilter.SMOOTH)
    background = Image.new("RGB", size, (246, 240, 223))
    ground = Image.new("RGB", size, (234, 217, 184))
    background.paste(ground, (0, height - 165))
    final = Image.alpha_composite(background.convert("RGBA"), shadow).convert("RGB")
    final.paste(model_image, (0, 0), model_mask.filter(ImageFilter.MaxFilter(3)))

    edge_overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(edge_overlay)
    for part_order, (mesh, _) in enumerate(parts):
        depth_bias = part_order * 0.01
        for start, end in visible_mesh_edges(mesh, screen, zbuffer, depth_bias):
            edge_draw.line((start[0], start[1], end[0], end[1]), fill=(72, 52, 27, 118), width=1)
    final = Image.alpha_composite(final.convert("RGBA"), edge_overlay).convert("RGB")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    final.save(out_path)


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
