#!/usr/bin/env python3
"""Build a maker-site release bundle for the Giza pyramid STL kit."""

from __future__ import annotations

import math
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
RELEASE = ROOT / "release" / "thingiverse"
BUNDLE_NAME = "giza-pyramid-construction-theory-stl-kit"
BUNDLE = RELEASE / "upload_bundle" / BUNDLE_NAME
ZIP_PATH = RELEASE / f"{BUNDLE_NAME}-v0.1.0.zip"
IMAGES = RELEASE / "images"

RENDER_FILES = [
    ("cover_full_ramp_system.png", DIST / "constructed_states" / "constructed_01_full_backfilled_ramp_system.stl"),
    ("capstone_before_deramping.png", DIST / "constructed_states" / "constructed_02_capstone_set_before_deramping.stl"),
    ("partial_top_down_deramping.png", DIST / "constructed_states" / "constructed_03_partial_top_down_deramping.stl"),
    ("finished_pyramid.png", DIST / "constructed_states" / "constructed_04_finished_pyramid.stl"),
]

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


def read_ascii_stl(path: Path) -> list[Triangle]:
    vertices: list[Vec3] = []
    for line in path.read_text(errors="ignore").splitlines():
        parts = line.strip().split()
        if len(parts) == 4 and parts[0] == "vertex":
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
    return [tuple(vertices[i : i + 3]) for i in range(0, len(vertices) - 2, 3)]  # type: ignore[misc]


def rotate(point: Vec3, yaw: float, pitch: float) -> Vec3:
    x, y, z = point
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    x1 = x * cy - y * sy
    y1 = x * sy + y * cy
    z1 = z
    return (x1, y1 * cp - z1 * sp, y1 * sp + z1 * cp)


def normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    ux, uy, uz = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    vx, vy, vz = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    mag = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / mag, ny / mag, nz / mag)


def render_stl(path: Path, out_path: Path, size: tuple[int, int] = (1600, 1000)) -> None:
    try:
        from PIL import Image, ImageDraw
    except Exception as exc:  # pragma: no cover - optional release nicety
        print(f"Skipping renders; Pillow is unavailable: {exc}")
        return

    triangles = read_ascii_stl(path)
    yaw = math.radians(-38)
    pitch = math.radians(30)
    projected = []
    xs: list[float] = []
    ys: list[float] = []
    for tri in triangles:
        transformed = [rotate(point, yaw, pitch) for point in tri]
        projected.append(transformed)
        xs.extend(point[0] for point in transformed)
        ys.extend(point[1] for point in transformed)

    if not projected:
        return

    width, height = size
    pad = 80
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    scale = min((width - pad * 2) / (max_x - min_x), (height - pad * 2) / (max_y - min_y))
    light = rotate((-0.35, -0.55, 1.0), yaw, pitch)
    light_mag = math.sqrt(sum(v * v for v in light)) or 1.0
    light = tuple(v / light_mag for v in light)

    image = Image.new("RGB", size, "#f6f0df")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, height - 165, width, height), fill="#ead9b8")

    def screen(point: Vec3) -> tuple[float, float]:
        return (
            pad + (point[0] - min_x) * scale,
            height - pad - (point[1] - min_y) * scale,
        )

    shaded = []
    for tri in projected:
        depth = sum(point[2] for point in tri) / 3.0
        n = normal(*tri)
        intensity = max(0.48, min(1.0, 0.55 + 0.45 * sum(n[i] * light[i] for i in range(3))))
        base = (205, 174, 105)
        color = tuple(max(0, min(255, int(channel * intensity))) for channel in base)
        shaded.append((depth, [screen(point) for point in tri], color))

    for _, points, color in sorted(shaded, key=lambda item: item[0]):
        draw.polygon(points, fill=color)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


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

    for name, source in RENDER_FILES:
        render_stl(source, IMAGES / name)

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
