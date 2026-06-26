#!/usr/bin/env python3
"""Generate a printable/viewable Giza construction theory STL kit.

The model is conceptual, not an archaeological proof. It turns a construction
sequence into parametric geometry:

1. A stepped inner mound/core with surrounding temporary fill.
2. Temporary switchback ramp material on all four sides.
3. A flat top platform and capstone.
4. Removable casing rings that can be added top-down as ramps are removed.
5. Optional stockpile/foundation pieces representing reusable ramp material.

No third-party Python packages are required. The script writes ASCII STL files.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable


Vec3 = tuple[float, float, float]
Triangle = tuple[Vec3, Vec3, Vec3]


@dataclass
class Mesh:
    name: str
    triangles: list[Triangle] = field(default_factory=list)

    def add_tri(self, a: Vec3, b: Vec3, c: Vec3) -> None:
        if triangle_area(a, b, c) > 0.000001:
            self.triangles.append((a, b, c))

    def add_quad(self, a: Vec3, b: Vec3, c: Vec3, d: Vec3) -> None:
        self.add_tri(a, b, c)
        self.add_tri(a, c, d)

    def extend(self, other: "Mesh") -> None:
        self.triangles.extend(other.triangles)

    def copy(self, name: str | None = None) -> "Mesh":
        return Mesh(name or self.name, list(self.triangles))

    def translated(self, dx: float, dy: float, dz: float, name: str | None = None) -> "Mesh":
        moved = Mesh(name or self.name)
        for tri in self.triangles:
            moved.triangles.append(tuple((x + dx, y + dy, z + dz) for x, y, z in tri))  # type: ignore[arg-type]
        return moved

    def print_pose(self, margin_mm: float = 2.0) -> "Mesh":
        min_x, min_y, min_z, _, _, _ = self.bounds()
        return self.translated(margin_mm - min_x, margin_mm - min_y, -min_z, self.name)

    def bounds(self) -> tuple[float, float, float, float, float, float]:
        xs: list[float] = []
        ys: list[float] = []
        zs: list[float] = []
        for tri in self.triangles:
            for x, y, z in tri:
                xs.append(x)
                ys.append(y)
                zs.append(z)
        if not xs:
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

    def write_ascii_stl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            fh.write(f"solid {safe_name(self.name)}\n")
            for a, b, c in self.triangles:
                nx, ny, nz = normal(a, b, c)
                fh.write(f"  facet normal {nx:.7g} {ny:.7g} {nz:.7g}\n")
                fh.write("    outer loop\n")
                fh.write(f"      vertex {a[0]:.7g} {a[1]:.7g} {a[2]:.7g}\n")
                fh.write(f"      vertex {b[0]:.7g} {b[1]:.7g} {b[2]:.7g}\n")
                fh.write(f"      vertex {c[0]:.7g} {c[1]:.7g} {c[2]:.7g}\n")
                fh.write("    endloop\n")
                fh.write("  endfacet\n")
            fh.write(f"endsolid {safe_name(self.name)}\n")


@dataclass(frozen=True)
class KitParams:
    base_mm: float = 160.0
    height_mm: float = 101.8
    capstone_height_mm: float = 7.0
    courses: int = 16
    casing_rings: int = 16
    core_base_fraction: float = 0.65
    core_top_fraction: float = 0.62
    casing_clearance_mm: float = 0.7
    min_casing_wall_mm: float = 1.2
    ramp_width_mm: float = 18.0
    ramp_gap_mm: float = 4.0
    ramp_thickness_mm: float = 2.8
    ramp_margin_mm: float = 6.0
    ramp_platform_fraction: float = 0.25
    landing_corner_notch_fraction: float = 0.35
    top_platform_half_fraction: float = 0.24
    temporary_overbuild_mm: float = 0.0
    platform_thickness_mm: float = 0.9
    output_dir: Path = Path("dist")

    @property
    def core_height_mm(self) -> float:
        return self.height_mm - self.capstone_height_mm

    @property
    def core_base_half_mm(self) -> float:
        return (self.base_mm / 2.0) * self.core_base_fraction

    @property
    def capstone_base_half_mm(self) -> float:
        return final_half(self, self.core_height_mm)

    @property
    def core_top_half_mm(self) -> float:
        return self.capstone_base_half_mm * self.core_top_fraction


def safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in name)


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(v: Vec3) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    n = cross(sub(b, a), sub(c, a))
    mag = length(n)
    if mag == 0:
        return (0.0, 0.0, 0.0)
    return (n[0] / mag, n[1] / mag, n[2] / mag)


def triangle_area(a: Vec3, b: Vec3, c: Vec3) -> float:
    return 0.5 * length(cross(sub(b, a), sub(c, a)))


def final_half(p: KitParams, z: float) -> float:
    return max(0.0, (p.base_mm / 2.0) * (1.0 - z / p.height_mm))


def requested_top_work_deck_half(p: KitParams) -> float:
    return max(p.capstone_base_half_mm + 4.0, p.base_mm * p.top_platform_half_fraction)


def temporary_overbuild_offset(p: KitParams) -> float:
    return max(0.0, p.temporary_overbuild_mm, requested_top_work_deck_half(p) - p.capstone_base_half_mm)


def top_work_deck_half(p: KitParams) -> float:
    return p.capstone_base_half_mm + temporary_overbuild_offset(p)


def temporary_work_half(p: KitParams, z: float) -> float:
    return final_half(p, z) + temporary_overbuild_offset(p)


def core_half_at_fraction(p: KitParams, t: float) -> float:
    t = min(1.0, max(0.0, t))
    return p.core_top_half_mm + (p.core_base_half_mm - p.core_top_half_mm) * (1.0 - t)


def course_z(p: KitParams, level: int) -> float:
    return p.core_height_mm * level / p.courses


def ramp_level_count(p: KitParams) -> int:
    return p.courses


def ramp_lane_count() -> int:
    return 1


def ramp_floor_z(p: KitParams, level: int) -> float:
    return max(0.0, course_z(p, level) - p.ramp_thickness_mm)


def ramp_top_z(p: KitParams, level: int) -> float:
    return course_z(p, level + 1)


def ramp_lane_bounds(p: KitParams, level: int, lane: int = 0) -> tuple[float, float]:
    if lane < 0 or lane >= ramp_lane_count():
        raise ValueError(f"Unsupported ramp lane: {lane}")
    z0 = course_z(p, level)
    z1 = course_z(p, level + 1)
    mid_z = (z0 + z1) / 2.0
    inner = temporary_work_half(p, mid_z) + p.ramp_gap_mm
    lane_gap = 0.0
    lane_width = (p.ramp_width_mm - lane_gap) / ramp_lane_count()
    lane_inner = inner + lane * (lane_width + lane_gap)
    lane_outer = lane_inner + lane_width
    return lane_inner, lane_outer


def ramp_band_outer_half(p: KitParams, level: int) -> float:
    _, outer = ramp_lane_bounds(p, level, ramp_lane_count() - 1)
    return outer


def square_corners(half: float, z: float) -> list[Vec3]:
    return [
        (-half, -half, z),
        (half, -half, z),
        (half, half, z),
        (-half, half, z),
    ]


def add_horizontal_square(mesh: Mesh, z: float, half: float, flip: bool = False) -> None:
    c = square_corners(half, z)
    if flip:
        mesh.add_quad(c[3], c[2], c[1], c[0])
    else:
        mesh.add_quad(c[0], c[1], c[2], c[3])


def add_horizontal_square_ring(mesh: Mesh, z: float, outer: float, inner: float) -> None:
    if inner <= 0.000001:
        add_horizontal_square(mesh, z, outer)
        return
    if inner >= outer:
        return
    # South, east, north, west strips around the central square opening.
    mesh.add_quad((-outer, -outer, z), (outer, -outer, z), (outer, -inner, z), (-outer, -inner, z))
    mesh.add_quad((inner, -inner, z), (outer, -inner, z), (outer, inner, z), (inner, inner, z))
    mesh.add_quad((-outer, inner, z), (outer, inner, z), (outer, outer, z), (-outer, outer, z))
    mesh.add_quad((-outer, -inner, z), (-inner, -inner, z), (-inner, inner, z), (-outer, inner, z))


def add_box(mesh: Mesh, xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float) -> None:
    if xmax <= xmin or ymax <= ymin or zmax <= zmin:
        return
    v = [
        (xmin, ymin, zmin),
        (xmax, ymin, zmin),
        (xmax, ymax, zmin),
        (xmin, ymax, zmin),
        (xmin, ymin, zmax),
        (xmax, ymin, zmax),
        (xmax, ymax, zmax),
        (xmin, ymax, zmax),
    ]
    mesh.add_quad(v[3], v[2], v[1], v[0])  # bottom
    mesh.add_quad(v[4], v[5], v[6], v[7])  # top
    mesh.add_quad(v[0], v[1], v[5], v[4])
    mesh.add_quad(v[1], v[2], v[6], v[5])
    mesh.add_quad(v[2], v[3], v[7], v[6])
    mesh.add_quad(v[3], v[0], v[4], v[7])


def polygon_area_xy(points: list[tuple[float, float]]) -> float:
    area = 0.0
    for i, (x0, y0) in enumerate(points):
        x1, y1 = points[(i + 1) % len(points)]
        area += x0 * y1 - x1 * y0
    return area / 2.0


def point_in_triangle_xy(
    point: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> bool:
    px, py = point
    ax, ay = a
    bx, by = b
    cx, cy = c
    denominator = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(denominator) < 0.0000001:
        return False
    w1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / denominator
    w2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / denominator
    w3 = 1.0 - w1 - w2
    return w1 >= -0.000001 and w2 >= -0.000001 and w3 >= -0.000001


def triangulate_polygon_xy(points: list[tuple[float, float]]) -> list[tuple[int, int, int]]:
    if len(points) < 3:
        return []
    if polygon_area_xy(points) < 0:
        points.reverse()

    indices = list(range(len(points)))
    triangles: list[tuple[int, int, int]] = []
    guard = 0
    while len(indices) > 3 and guard < 100:
        guard += 1
        clipped = False
        for pos, current in enumerate(indices):
            prev_i = indices[pos - 1]
            next_i = indices[(pos + 1) % len(indices)]
            ax, ay = points[prev_i]
            bx, by = points[current]
            cx, cy = points[next_i]
            cross_z = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            if cross_z <= 0:
                continue
            if any(
                point_i not in (prev_i, current, next_i)
                and point_in_triangle_xy(points[point_i], points[prev_i], points[current], points[next_i])
                for point_i in indices
            ):
                continue
            triangles.append((prev_i, current, next_i))
            del indices[pos]
            clipped = True
            break
        if not clipped:
            break
    if len(indices) == 3:
        triangles.append((indices[0], indices[1], indices[2]))
    return triangles


def add_vertical_prism(mesh: Mesh, points: list[tuple[float, float]], zmin: float, zmax: float) -> None:
    if zmax <= zmin or len(points) < 3:
        return
    if polygon_area_xy(points) < 0:
        points = list(reversed(points))

    bottom = [(x, y, zmin) for x, y in points]
    top = [(x, y, zmax) for x, y in points]
    for i, j, k in triangulate_polygon_xy(list(points)):
        mesh.add_tri(top[i], top[j], top[k])
        mesh.add_tri(bottom[k], bottom[j], bottom[i])
    for i in range(len(points)):
        j = (i + 1) % len(points)
        mesh.add_quad(bottom[i], bottom[j], top[j], top[i])


def add_oriented_box(
    mesh: Mesh,
    transform: Callable[[float, float, float], Vec3],
    umin: float,
    umax: float,
    vmin: float,
    vmax: float,
    zmin: float,
    zmax: float,
) -> None:
    if umax <= umin or vmax <= vmin or zmax <= zmin:
        return
    corners = [
        transform(umin, vmin, zmin),
        transform(umax, vmin, zmin),
        transform(umax, vmax, zmin),
        transform(umin, vmax, zmin),
        transform(umin, vmin, zmax),
        transform(umax, vmin, zmax),
        transform(umax, vmax, zmax),
        transform(umin, vmax, zmax),
    ]
    faces = [
        (3, 2, 1, 0),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    for a, b, c, d in faces:
        mesh.add_quad(corners[a], corners[b], corners[c], corners[d])


def add_square_frustum_solid(mesh: Mesh, z0: float, z1: float, half0: float, half1: float) -> None:
    if half0 <= 0 or z1 <= z0:
        return
    bottom = square_corners(half0, z0)
    if half1 <= 0.000001:
        apex = (0.0, 0.0, z1)
        mesh.add_quad(bottom[3], bottom[2], bottom[1], bottom[0])
        for i in range(4):
            mesh.add_tri(bottom[i], bottom[(i + 1) % 4], apex)
        return
    top = square_corners(half1, z1)
    mesh.add_quad(bottom[3], bottom[2], bottom[1], bottom[0])
    mesh.add_quad(top[0], top[1], top[2], top[3])
    for i in range(4):
        mesh.add_quad(bottom[i], bottom[(i + 1) % 4], top[(i + 1) % 4], top[i])


def add_square_frustum_sides(mesh: Mesh, z0: float, z1: float, half0: float, half1: float) -> None:
    if half0 <= 0 or half1 <= 0 or z1 <= z0:
        return
    bottom = square_corners(half0, z0)
    top = square_corners(half1, z1)
    for i in range(4):
        mesh.add_quad(bottom[i], bottom[(i + 1) % 4], top[(i + 1) % 4], top[i])


def add_square_frustum_shell(
    mesh: Mesh,
    z0: float,
    z1: float,
    outer0: float,
    outer1: float,
    inner0: float,
    inner1: float,
    include_caps: bool = True,
) -> None:
    if z1 <= z0 or outer0 <= 0 or outer1 <= 0:
        return
    inner0 = max(0.0, min(inner0, outer0 - 0.01))
    inner1 = max(0.0, min(inner1, outer1 - 0.01))
    outer_bottom = square_corners(outer0, z0)
    outer_top = square_corners(outer1, z1)
    inner_bottom = square_corners(inner0, z0)
    inner_top = square_corners(inner1, z1)

    for i in range(4):
        j = (i + 1) % 4
        mesh.add_quad(outer_bottom[i], outer_bottom[j], outer_top[j], outer_top[i])
        mesh.add_quad(inner_bottom[j], inner_bottom[i], inner_top[i], inner_top[j])
        if include_caps:
            mesh.add_quad(outer_bottom[j], outer_bottom[i], inner_bottom[i], inner_bottom[j])
            mesh.add_quad(outer_top[i], outer_top[j], inner_top[j], inner_top[i])


def add_stepped_core_course(mesh: Mesh, p: KitParams, level: int) -> None:
    dz = p.core_height_mm / p.courses
    z0 = level * dz
    z1 = (level + 1) * dz
    half = core_half_at_fraction(p, level / p.courses)
    next_half = core_half_at_fraction(p, (level + 1) / p.courses)

    if level == 0:
        add_horizontal_square(mesh, 0.0, half, flip=True)

    mesh.add_quad((-half, -half, z0), (half, -half, z0), (half, -half, z1), (-half, -half, z1))
    mesh.add_quad((half, -half, z0), (half, half, z0), (half, half, z1), (half, -half, z1))
    mesh.add_quad((half, half, z0), (-half, half, z0), (-half, half, z1), (half, half, z1))
    mesh.add_quad((-half, half, z0), (-half, -half, z0), (-half, -half, z1), (-half, half, z1))

    add_horizontal_square_ring(mesh, z1, half, next_half)
    if level == p.courses - 1:
        add_horizontal_square(mesh, z1, next_half)


def make_stepped_core_layer(p: KitParams, level: int) -> Mesh:
    mesh = Mesh(f"inner_stepped_mound_layer_{level + 1:02d}")
    add_stepped_core_course(mesh, p, level)
    return mesh


def make_stepped_core(p: KitParams) -> Mesh:
    mesh = Mesh("inner_stepped_mound_core")
    for i in range(p.courses):
        add_stepped_core_course(mesh, p, i)
    return mesh


def make_display_stepped_core(p: KitParams) -> Mesh:
    mesh = Mesh("display_inner_core_blended_to_capstone")
    for i in range(p.courses - 1):
        add_stepped_core_course(mesh, p, i)
    z0 = course_z(p, p.courses - 1)
    z1 = p.core_height_mm
    half0 = core_half_at_fraction(p, (p.courses - 1) / p.courses)
    add_square_frustum_sides(mesh, z0, z1, half0, p.capstone_base_half_mm)
    return mesh


def backfill_half_at_level(p: KitParams, level: int) -> float:
    level = min(max(level, 0), p.courses)
    if level == p.courses:
        return top_work_deck_half(p) + p.ramp_gap_mm + p.ramp_width_mm
    return ramp_band_outer_half(p, level)


def make_temporary_backfill(p: KitParams, max_z: float | None = None) -> Mesh:
    mesh = Mesh("temporary_ramp_backfill")
    for i in range(p.courses):
        z0 = course_z(p, i)
        z1 = course_z(p, i + 1)
        if max_z is not None and z1 > max_z:
            continue
        half = backfill_half_at_level(p, i)
        next_half = backfill_half_at_level(p, i + 1)

        if i == 0:
            add_horizontal_square(mesh, 0.0, half, flip=True)

        mesh.add_quad((-half, -half, z0), (half, -half, z0), (half, -half, z1), (-half, -half, z1))
        mesh.add_quad((half, -half, z0), (half, half, z0), (half, half, z1), (half, -half, z1))
        mesh.add_quad((half, half, z0), (-half, half, z0), (-half, half, z1), (half, half, z1))
        mesh.add_quad((-half, half, z0), (-half, -half, z0), (-half, -half, z1), (-half, half, z1))

        add_horizontal_square_ring(mesh, z1, half, next_half)
        if i == p.courses - 1:
            add_horizontal_square(mesh, z1, next_half)
    return mesh


Rect2 = tuple[float, float, float, float]


def ramp_cut_rects_for_level(p: KitParams, level: int) -> list[Rect2]:
    inner, outer = ramp_lane_bounds(p, level, 0)
    return [
        (-inner, inner, inner, outer),  # north side ramp
        (inner, outer, -inner, inner),  # east side ramp
        (-inner, inner, -outer, -inner),  # south side ramp
        (-outer, -inner, -inner, inner),  # west side ramp
        (inner, outer, inner, outer),  # ne notched platform zone
        (inner, outer, -outer, -inner),  # se notched platform zone
        (-outer, -inner, -outer, -inner),  # sw notched platform zone
        (-outer, -inner, inner, outer),  # nw notched platform zone
    ]


def rects_intersect(a: Rect2, b: Rect2) -> bool:
    ax0, ax1, ay0, ay1 = a
    bx0, bx1, by0, by1 = b
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


def point_in_rect(x: float, y: float, rect: Rect2) -> bool:
    xmin, xmax, ymin, ymax = rect
    return xmin <= x <= xmax and ymin <= y <= ymax


def slab_cut_rects(p: KitParams, slab_level: int) -> list[Rect2]:
    levels = {slab_level}
    if slab_level + 1 < ramp_level_count(p):
        levels.add(slab_level + 1)
    rects: list[Rect2] = []
    for level in sorted(levels):
        rects.extend(ramp_cut_rects_for_level(p, level))
    return rects


def add_cut_square_slab(mesh: Mesh, half: float, z0: float, z1: float, cut_rects: list[Rect2]) -> None:
    bounds = (-half, half, -half, half)
    active_cuts = [rect for rect in cut_rects if rects_intersect(bounds, rect)]
    xs = {-half, half}
    ys = {-half, half}
    for xmin, xmax, ymin, ymax in active_cuts:
        xs.add(max(-half, min(half, xmin)))
        xs.add(max(-half, min(half, xmax)))
        ys.add(max(-half, min(half, ymin)))
        ys.add(max(-half, min(half, ymax)))

    x_values = sorted(xs)
    y_values = sorted(ys)
    for xi in range(len(x_values) - 1):
        xmin = x_values[xi]
        xmax = x_values[xi + 1]
        if xmax <= xmin:
            continue
        for yi in range(len(y_values) - 1):
            ymin = y_values[yi]
            ymax = y_values[yi + 1]
            if ymax <= ymin:
                continue
            cx = (xmin + xmax) / 2.0
            cy = (ymin + ymax) / 2.0
            if any(point_in_rect(cx, cy, rect) for rect in active_cuts):
                continue
            add_box(mesh, xmin, xmax, ymin, ymax, z0, z1)


def make_cut_temporary_backfill(p: KitParams, max_z: float | None = None) -> Mesh:
    mesh = Mesh("temporary_stepped_mound_cut_for_ramps")
    for i in range(p.courses):
        z0 = course_z(p, i)
        z1 = course_z(p, i + 1)
        if max_z is not None and z1 > max_z:
            continue
        half = backfill_half_at_level(p, i)
        add_cut_square_slab(mesh, half, z0, z1, slab_cut_rects(p, i))
    return mesh


def make_cut_temporary_backfill_layer(p: KitParams, level: int) -> Mesh:
    mesh = Mesh(f"temporary_cut_stepped_mound_layer_{level + 1:02d}")
    z0 = course_z(p, level)
    z1 = course_z(p, level + 1)
    half = backfill_half_at_level(p, level)
    add_cut_square_slab(mesh, half, z0, z1, slab_cut_rects(p, level))
    return mesh


def make_casing_ring(p: KitParams, ring_index_bottom_up: int, include_caps: bool = True) -> Mesh:
    mesh = Mesh(f"casing_ring_{ring_index_bottom_up + 1:02d}_bottom_up")
    z0 = p.core_height_mm * ring_index_bottom_up / p.casing_rings
    z1 = p.core_height_mm * (ring_index_bottom_up + 1) / p.casing_rings
    outer0 = final_half(p, z0)
    outer1 = final_half(p, z1)
    inner0 = core_half_at_fraction(p, z0 / p.core_height_mm) + p.casing_clearance_mm
    inner1 = core_half_at_fraction(p, z1 / p.core_height_mm) + p.casing_clearance_mm
    inner0 = min(inner0, outer0 - p.min_casing_wall_mm)
    inner1 = min(inner1, outer1 - p.min_casing_wall_mm)
    add_square_frustum_shell(mesh, z0, z1, outer0, outer1, inner0, inner1, include_caps=include_caps)
    return mesh


def face_transform(face: int) -> Callable[[float, float, float], Vec3]:
    # Local u runs along a face. Local v points outward from the pyramid.
    if face == 0:  # north, +Y
        return lambda u, v, z: (u, v, z)
    if face == 1:  # east, +X
        return lambda u, v, z: (v, -u, z)
    if face == 2:  # south, -Y
        return lambda u, v, z: (-u, -v, z)
    if face == 3:  # west, -X
        return lambda u, v, z: (-v, u, z)
    raise ValueError(f"Unsupported face index: {face}")


def add_oriented_wedge(
    mesh: Mesh,
    transform: Callable[[float, float, float], Vec3],
    umin: float,
    umax: float,
    v0: float,
    v1: float,
    bottom_z: float,
    top_z_at_umin: float,
    top_z_at_umax: float,
) -> None:
    # Keep vertex order tied to geometric min/max coordinates, not the ramp's
    # travel direction. Otherwise alternate switchbacks wind inside-out.
    p0 = transform(umin, v0, bottom_z)
    p1 = transform(umax, v0, bottom_z)
    p2 = transform(umax, v1, bottom_z)
    p3 = transform(umin, v1, bottom_z)
    t0 = transform(umin, v0, top_z_at_umin)
    t1 = transform(umax, v0, top_z_at_umax)
    t2 = transform(umax, v1, top_z_at_umax)
    t3 = transform(umin, v1, top_z_at_umin)
    mesh.add_quad(p3, p2, p1, p0)  # bottom
    mesh.add_quad(t0, t1, t2, t3)  # sloped top
    mesh.add_quad(p0, p1, t1, t0)
    mesh.add_quad(p1, p2, t2, t1)
    mesh.add_quad(p2, p3, t3, t2)
    mesh.add_quad(p3, p0, t0, t3)


def add_face_from_vertices(mesh: Mesh, vertices: list[Vec3], solid_center: Vec3) -> None:
    if len(vertices) < 3:
        return
    anchor = vertices[0]
    for i in range(1, len(vertices) - 1):
        a, b, c = anchor, vertices[i], vertices[i + 1]
        n = normal(a, b, c)
        tri_center = (
            (a[0] + b[0] + c[0]) / 3.0,
            (a[1] + b[1] + c[1]) / 3.0,
            (a[2] + b[2] + c[2]) / 3.0,
        )
        outward = sub(tri_center, solid_center)
        if n[0] * outward[0] + n[1] * outward[1] + n[2] * outward[2] < 0:
            mesh.add_tri(a, c, b)
        else:
            mesh.add_tri(a, b, c)


def add_yz_tunnel(mesh: Mesh, y0: float, z0: float, y1: float, z1: float, width: float, height: float) -> None:
    length_yz = math.hypot(y1 - y0, z1 - z0)
    if length_yz <= 0.000001 or width <= 0 or height <= 0:
        return
    normal_y = -(z1 - z0) / length_yz
    normal_z = (y1 - y0) / length_yz
    half_width = width / 2.0
    half_height = height / 2.0

    def section(y: float, z: float) -> list[Vec3]:
        low_y = y - normal_y * half_height
        low_z = z - normal_z * half_height
        high_y = y + normal_y * half_height
        high_z = z + normal_z * half_height
        return [
            (-half_width, low_y, low_z),
            (half_width, low_y, low_z),
            (half_width, high_y, high_z),
            (-half_width, high_y, high_z),
        ]

    start = section(y0, z0)
    end = section(y1, z1)
    all_points = start + end
    center = (
        sum(point[0] for point in all_points) / len(all_points),
        sum(point[1] for point in all_points) / len(all_points),
        sum(point[2] for point in all_points) / len(all_points),
    )
    faces = [
        [start[0], start[1], start[2], start[3]],
        [end[3], end[2], end[1], end[0]],
        [start[0], end[0], end[1], start[1]],
        [start[1], end[1], end[2], start[2]],
        [start[2], end[2], end[3], start[3]],
        [start[3], end[3], end[0], start[0]],
    ]
    for face in faces:
        add_face_from_vertices(mesh, face, center)


def add_gabled_chamber(
    mesh: Mesh,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    zmin: float,
    wall_zmax: float,
    apex_z: float,
) -> None:
    add_box(mesh, xmin, xmax, ymin, ymax, zmin, wall_zmax)
    if apex_z <= wall_zmax:
        return
    ridge_x = (xmin + xmax) / 2.0
    roof_points = [
        (xmin, ymin, wall_zmax),
        (xmax, ymin, wall_zmax),
        (xmax, ymax, wall_zmax),
        (xmin, ymax, wall_zmax),
        (ridge_x, ymin, apex_z),
        (ridge_x, ymax, apex_z),
    ]
    center = (
        sum(point[0] for point in roof_points) / len(roof_points),
        sum(point[1] for point in roof_points) / len(roof_points),
        sum(point[2] for point in roof_points) / len(roof_points),
    )
    for face in (
        [roof_points[0], roof_points[4], roof_points[5], roof_points[3]],
        [roof_points[1], roof_points[2], roof_points[5], roof_points[4]],
        [roof_points[0], roof_points[1], roof_points[4]],
        [roof_points[3], roof_points[5], roof_points[2]],
    ):
        add_face_from_vertices(mesh, list(face), center)


def add_oriented_ramp_with_platform(
    mesh: Mesh,
    transform: Callable[[float, float, float], Vec3],
    low_u: float,
    high_u: float,
    v0: float,
    v1: float,
    bottom_z: float,
    low_z: float,
    high_z: float,
    platform_fraction: float,
) -> None:
    platform_fraction = min(0.75, max(0.05, platform_fraction))
    break_u = low_u + (1.0 - platform_fraction) * (high_u - low_u)
    raw_points = [
        (low_u, v0, bottom_z),
        (break_u, v0, bottom_z),
        (high_u, v0, bottom_z),
        (high_u, v1, bottom_z),
        (break_u, v1, bottom_z),
        (low_u, v1, bottom_z),
        (low_u, v0, low_z),
        (break_u, v0, high_z),
        (high_u, v0, high_z),
        (high_u, v1, high_z),
        (break_u, v1, high_z),
        (low_u, v1, low_z),
    ]
    pts = [transform(*point) for point in raw_points]
    center = (
        sum(point[0] for point in pts) / len(pts),
        sum(point[1] for point in pts) / len(pts),
        sum(point[2] for point in pts) / len(pts),
    )

    # Split colinear bottom and side runs into rectangles. A single polygon fan
    # would create degenerate triangles and leave open STL edges.
    for face_vertices in (
        [pts[0], pts[1], pts[4], pts[5]],
        [pts[1], pts[2], pts[3], pts[4]],
        [pts[6], pts[7], pts[10], pts[11]],
        [pts[7], pts[8], pts[9], pts[10]],
        [pts[0], pts[1], pts[7], pts[6]],
        [pts[1], pts[2], pts[8], pts[7]],
        [pts[5], pts[4], pts[10], pts[11]],
        [pts[4], pts[3], pts[9], pts[10]],
        [pts[5], pts[0], pts[6], pts[11]],
        [pts[2], pts[3], pts[9], pts[8]],
    ):
        add_face_from_vertices(mesh, face_vertices, center)


def make_ramp_segment(p: KitParams, face: int, level: int, lane: int = 0) -> Mesh:
    transform = face_transform(face)
    z0 = course_z(p, level)
    inner, outer = ramp_lane_bounds(p, level, lane)
    umin = -inner
    umax = inner
    v0 = inner
    v1 = outer
    bottom_z = ramp_floor_z(p, level)
    heights = ramp_corner_heights(p, level, lane)
    face_corners = [
        ("nw", "ne"),
        ("ne", "se"),
        ("se", "sw"),
        ("sw", "nw"),
    ]
    left_z = heights[face_corners[face][0]]
    right_z = heights[face_corners[face][1]]
    mesh = Mesh(f"ramp_face_{face + 1}_level_{level + 1:02d}")
    if left_z <= right_z:
        add_oriented_ramp_with_platform(
            mesh,
            transform,
            umin,
            umax,
            v0,
            v1,
            bottom_z,
            left_z,
            right_z,
            p.ramp_platform_fraction,
        )
    else:
        add_oriented_ramp_with_platform(
            mesh,
            transform,
            umax,
            umin,
            v0,
            v1,
            bottom_z,
            right_z,
            left_z,
            p.ramp_platform_fraction,
        )
    return mesh


def ramp_corner_heights(p: KitParams, level: int, lane: int = 0) -> dict[str, float]:
    z0 = course_z(p, level)
    z1 = ramp_top_z(p, level)
    low = max(z0, min(z0 + 0.9, z1 - 0.2)) if level == 0 else z0
    if (level + lane) % 2 == 0:
        return {"nw": low, "ne": z1, "se": low, "sw": z1}
    return {"nw": z1, "ne": low, "se": z1, "sw": low}


def add_notched_corner_landing(
    mesh: Mesh,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    zmin: float,
    zmax: float,
    corner: str,
    notch_fraction: float,
) -> None:
    if zmax <= zmin:
        return
    notch_fraction = min(0.7, max(0.05, notch_fraction))
    width = xmax - xmin
    depth = ymax - ymin
    notch_w = width * notch_fraction
    notch_d = depth * notch_fraction

    if corner == "ne":
        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax - notch_d), (xmax - notch_w, ymax - notch_d), (xmax - notch_w, ymax), (xmin, ymax)]
    elif corner == "se":
        points = [(xmin, ymin), (xmax - notch_w, ymin), (xmax - notch_w, ymin + notch_d), (xmax, ymin + notch_d), (xmax, ymax), (xmin, ymax)]
    elif corner == "sw":
        points = [(xmin + notch_w, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin + notch_d), (xmin + notch_w, ymin + notch_d)]
    elif corner == "nw":
        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin + notch_w, ymax), (xmin + notch_w, ymax - notch_d), (xmin, ymax - notch_d)]
    else:
        raise ValueError(f"Unsupported corner: {corner}")
    add_vertical_prism(mesh, points, zmin, zmax)


def make_corner_landing(p: KitParams, corner: str, level: int, lane: int = 0) -> Mesh:
    z0 = course_z(p, level)
    inner, outer = ramp_lane_bounds(p, level, lane)
    bottom_z = ramp_floor_z(p, level)
    top_z = ramp_corner_heights(p, level, lane)[corner]
    mesh = Mesh(f"ramp_corner_{corner}_level_{level + 1:02d}")
    bounds = {
        "ne": (inner, outer, inner, outer),
        "se": (inner, outer, -outer, -inner),
        "sw": (-outer, -inner, -outer, -inner),
        "nw": (-outer, -inner, inner, outer),
    }[corner]
    add_notched_corner_landing(mesh, bounds[0], bounds[1], bounds[2], bounds[3], bottom_z, top_z, corner, p.landing_corner_notch_fraction)
    return mesh


def make_side_ramp_underfill(p: KitParams, face: int, max_z: float | None = None) -> Mesh:
    face_names = ["north", "east", "south", "west"]
    mesh = Mesh(f"temporary_switchback_ramp_underfill_{face_names[face]}")
    transform = face_transform(face)
    for level in range(1, ramp_level_count(p)):
        if max_z is not None and ramp_top_z(p, level) > max_z:
            continue
        _, outer = ramp_lane_bounds(p, level, 0)
        inner = temporary_work_half(p, course_z(p, level)) + p.ramp_gap_mm
        zmin = course_z(p, level - 1)
        zmax = course_z(p, level)
        add_oriented_box(mesh, transform, -outer, outer, inner, outer, zmin, zmax)
    return mesh


def make_side_ramp_underfill_layer(p: KitParams, face: int, level: int) -> Mesh:
    face_names = ["north", "east", "south", "west"]
    mesh = Mesh(f"temporary_switchback_ramp_underfill_{face_names[face]}_layer_{level + 1:02d}")
    if level <= 0:
        return mesh
    transform = face_transform(face)
    _, outer = ramp_lane_bounds(p, level, 0)
    inner = temporary_work_half(p, course_z(p, level)) + p.ramp_gap_mm
    zmin = course_z(p, level - 1)
    zmax = course_z(p, level)
    add_oriented_box(mesh, transform, -outer, outer, inner, outer, zmin, zmax)
    return mesh


def make_corner_ramp_underfill(p: KitParams, corner: str, level: int) -> Mesh:
    inner, outer = ramp_lane_bounds(p, level, 0)
    zmin = course_z(p, level - 1)
    zmax = course_z(p, level)
    mesh = Mesh(f"temporary_switchback_corner_underfill_{corner}_level_{level + 1:02d}")
    bounds = {
        "ne": (inner, outer, inner, outer),
        "se": (inner, outer, -outer, -inner),
        "sw": (-outer, -inner, -outer, -inner),
        "nw": (-outer, -inner, inner, outer),
    }[corner]
    add_notched_corner_landing(mesh, bounds[0], bounds[1], bounds[2], bounds[3], zmin, zmax, corner, p.landing_corner_notch_fraction)
    return mesh


def make_ramp_underfill_layer(p: KitParams, level: int) -> Mesh:
    mesh = Mesh(f"temporary_switchback_ramp_underfill_layer_{level + 1:02d}")
    if level <= 0:
        return mesh
    for face in range(4):
        mesh.extend(make_side_ramp_underfill_layer(p, face, level))
    for corner in ("ne", "se", "sw", "nw"):
        mesh.extend(make_corner_ramp_underfill(p, corner, level))
    return mesh


def make_ramp_underfill(p: KitParams, max_z: float | None = None) -> tuple[Mesh, dict[str, Mesh]]:
    all_underfill = Mesh("temporary_switchback_ramp_underfill_all_sides")
    face_underfills: dict[str, Mesh] = {}
    face_names = ["north", "east", "south", "west"]
    for face, face_name in enumerate(face_names):
        side = make_side_ramp_underfill(p, face, max_z)
        face_underfills[face_name] = side
        all_underfill.extend(side)

    corner_underfill = Mesh("temporary_switchback_corner_underfill")
    for level in range(1, ramp_level_count(p)):
        if max_z is not None and ramp_top_z(p, level) > max_z:
            continue
        for corner in ("ne", "se", "sw", "nw"):
            support = make_corner_ramp_underfill(p, corner, level)
            corner_underfill.extend(support)
            all_underfill.extend(support)
    face_underfills["corner_landings"] = corner_underfill
    return all_underfill, face_underfills


def make_ramps(p: KitParams, max_z: float | None = None) -> tuple[Mesh, dict[str, Mesh], dict[str, Mesh]]:
    all_ramps = Mesh("temporary_switchback_ramps_all_sides")
    face_meshes: dict[str, Mesh] = {}
    segment_meshes: dict[str, Mesh] = {}
    face_names = ["north", "east", "south", "west"]
    for face in range(4):
        face_mesh = Mesh(f"temporary_switchback_ramps_{face_names[face]}")
        for level in range(ramp_level_count(p)):
            z1 = ramp_top_z(p, level)
            if max_z is not None and z1 > max_z:
                continue
            for lane in range(ramp_lane_count()):
                segment = make_ramp_segment(p, face, level, lane)
                segment_name = f"ramp_{face_names[face]}_level_{level + 1:02d}"
                segment_meshes[segment_name] = segment
                face_mesh.extend(segment)
                all_ramps.extend(segment)
        face_meshes[face_names[face]] = face_mesh

    corner_mesh = Mesh("temporary_switchback_corner_landings")
    for level in range(ramp_level_count(p)):
        z1 = ramp_top_z(p, level)
        if max_z is not None and z1 > max_z:
            continue
        for corner in ("ne", "se", "sw", "nw"):
            for lane in range(ramp_lane_count()):
                landing = make_corner_landing(p, corner, level, lane)
                if not landing.triangles:
                    continue
                segment_name = f"corner_{corner}_level_{level + 1:02d}"
                segment_meshes[segment_name] = landing
                corner_mesh.extend(landing)
                all_ramps.extend(landing)
    face_meshes["corner_landings"] = corner_mesh
    return all_ramps, face_meshes, segment_meshes


def make_ramp_layer(p: KitParams, level: int) -> Mesh:
    mesh = Mesh(f"temporary_switchback_ramp_layer_{level + 1:02d}")
    mesh.extend(make_ramp_underfill_layer(p, level))
    for face in range(4):
        mesh.extend(make_ramp_segment(p, face, level, 0))
    for corner in ("ne", "se", "sw", "nw"):
        mesh.extend(make_corner_landing(p, corner, level, 0))
    return mesh


def make_platform(p: KitParams) -> Mesh:
    mesh = Mesh("temporary_flat_capstone_platform")
    inner, _ = ramp_lane_bounds(p, p.courses - 1, 0)
    half = max(p.capstone_base_half_mm + 3.2, inner - 0.35)
    z1 = p.core_height_mm
    add_box(mesh, -half, half, -half, half, z1 - p.platform_thickness_mm, z1)
    return mesh


def make_capstone(p: KitParams) -> Mesh:
    mesh = Mesh("capstone")
    add_square_frustum_solid(mesh, p.core_height_mm, p.height_mm, p.capstone_base_half_mm, 0.0)
    return mesh


def make_finished_pyramid_surface(p: KitParams) -> Mesh:
    mesh = Mesh("finished_pyramid_smooth_surface")
    add_square_frustum_solid(mesh, 0.0, p.height_mm, p.base_mm / 2.0, 0.0)
    return mesh


def make_reuse_stockpile(p: KitParams) -> Mesh:
    mesh = Mesh("reuse_material_stockpile_for_next_pyramid")
    block_w = 14.0
    block_d = 10.0
    block_h = 5.0
    start_x = p.base_mm / 2.0 + 18.0
    start_y = -p.base_mm / 2.0
    for layer in range(3):
        cols = 4 - layer
        rows = 3 - min(layer, 1)
        for row in range(rows):
            for col in range(cols):
                x0 = start_x + col * (block_w + 1.2) + layer * 3.0
                y0 = start_y + row * (block_d + 1.2) + layer * 2.0
                z0 = layer * block_h
                add_box(mesh, x0, x0 + block_w, y0, y0 + block_d, z0, z0 + block_h)
    return mesh


def make_next_foundation_seed(p: KitParams) -> Mesh:
    mesh = Mesh("next_pyramid_seed_foundation_from_removed_ramp_material")
    tile = 9.0
    gap = 0.8
    start_x = p.base_mm / 2.0 + 18.0
    start_y = 8.0
    for row in range(5):
        for col in range(5):
            inset = abs(row - 2) + abs(col - 2)
            if inset > 4:
                continue
            z0 = 0.0
            x0 = start_x + col * (tile + gap)
            y0 = start_y + row * (tile + gap)
            add_box(mesh, x0, x0 + tile, y0, y0 + tile, z0, z0 + 2.4)
    return mesh


def make_internal_chambers_reference(p: KitParams, zmin_mm: float | None = None, zmax_mm: float | None = None, name: str = "internal_chambers_reference") -> Mesh:
    mesh = Mesh(name)
    real_height_m = 146.6
    real_base_m = 230.33
    scale = p.height_mm / real_height_m
    cubit_m = 0.5236
    clip_min_m = zmin_mm / scale if zmin_mm is not None else None
    clip_max_m = zmax_mm / scale if zmax_mm is not None else None

    def m(value: float) -> float:
        return value * scale

    def surface_half_m(z_m: float) -> float:
        return (real_base_m / 2.0) * (1.0 - z_m / real_height_m)

    def clipped_range(z0: float, z1: float) -> tuple[float, float] | None:
        lo = min(z0, z1)
        hi = max(z0, z1)
        if clip_min_m is not None:
            lo = max(lo, clip_min_m)
        if clip_max_m is not None:
            hi = min(hi, clip_max_m)
        if hi <= lo:
            return None
        return lo, hi

    def tunnel(y0: float, z0: float, y1: float, z1: float, width: float, height: float) -> None:
        if clip_min_m is not None or clip_max_m is not None:
            min_z = clip_min_m if clip_min_m is not None else -1_000_000.0
            max_z = clip_max_m if clip_max_m is not None else 1_000_000.0
            if abs(z1 - z0) < 0.000001:
                if z0 < min_z or z0 > max_z:
                    return
            else:
                ta = (min_z - z0) / (z1 - z0)
                tb = (max_z - z0) / (z1 - z0)
                t0 = max(0.0, min(ta, tb))
                t1 = min(1.0, max(ta, tb))
                if t1 <= t0:
                    return
                original_y0, original_z0 = y0, z0
                y0 = original_y0 + (y1 - original_y0) * t0
                z0 = original_z0 + (z1 - original_z0) * t0
                y1 = original_y0 + (y1 - original_y0) * t1
                z1 = original_z0 + (z1 - original_z0) * t1
        add_yz_tunnel(mesh, m(y0), m(z0), m(y1), m(z1), max(m(width), 1.15), max(m(height), 1.15))

    def chamber_box(center_y: float, z_floor: float, width_x: float, depth_y: float, height: float) -> None:
        z_range = clipped_range(z_floor, z_floor + height)
        if z_range is None:
            return
        z0, z1 = z_range
        add_box(
            mesh,
            -m(width_x / 2.0),
            m(width_x / 2.0),
            m(center_y - depth_y / 2.0),
            m(center_y + depth_y / 2.0),
            m(z0),
            m(z1),
        )

    def gabled_chamber(center_y: float, z_floor: float, width_x: float, depth_y: float, wall_height: float, apex_height: float) -> None:
        if clip_min_m is None and clip_max_m is None:
            add_gabled_chamber(
                mesh,
                -m(width_x / 2.0),
                m(width_x / 2.0),
                m(center_y - depth_y / 2.0),
                m(center_y + depth_y / 2.0),
                m(z_floor),
                m(z_floor + wall_height),
                m(z_floor + apex_height),
            )
            return
        chamber_box(center_y, z_floor, width_x, depth_y, wall_height)
        roof_range = clipped_range(z_floor + wall_height, z_floor + apex_height)
        if roof_range is not None:
            z0, z1 = roof_range
            add_box(
                mesh,
                -m(width_x / 2.0),
                m(width_x / 2.0),
                m(center_y - depth_y / 2.0),
                m(center_y + depth_y / 2.0),
                m(z0),
                m(z1),
            )

    desc_angle = math.radians(26.565)
    asc_angle = math.radians(26.1)

    entrance_z = 17.0
    entrance_y = surface_half_m(entrance_z)
    branch_y = entrance_y - 28.0 * math.cos(desc_angle)
    branch_z = entrance_z - 28.0 * math.sin(desc_angle)
    desc_end_y = branch_y - 72.0 * math.cos(desc_angle)
    desc_end_z = branch_z - 72.0 * math.sin(desc_angle)
    sub_entry_y = desc_end_y - 8.84

    asc_len = 75.0 * cubit_m
    asc_end_y = branch_y - asc_len * math.cos(asc_angle)
    asc_end_z = branch_z + asc_len * math.sin(asc_angle)
    gallery_end_y = asc_end_y - 46.68 * math.cos(asc_angle)
    gallery_end_z = asc_end_z + 46.68 * math.sin(asc_angle)

    passage_width = 2.0 * cubit_m
    passage_height = 1.2
    tunnel(entrance_y, entrance_z, branch_y, branch_z, passage_width, passage_height)
    tunnel(branch_y, branch_z, desc_end_y, desc_end_z, passage_width, passage_height)
    tunnel(desc_end_y, desc_end_z, sub_entry_y, desc_end_z, 0.85, 0.95)
    tunnel(branch_y, branch_z, asc_end_y, asc_end_z, passage_width, passage_height)

    sub_floor = -27.0
    sub_center_y = sub_entry_y - 2.0
    chamber_box(sub_center_y, sub_floor, 27.0 * cubit_m, 16.0 * cubit_m, 4.0)

    queen_floor = 20.9
    queen_center_y = 0.0
    queen_width_x = 11.0 * cubit_m
    queen_depth_y = 10.0 * cubit_m
    tunnel(asc_end_y, asc_end_z, queen_center_y + queen_depth_y / 2.0, queen_floor + 1.25, passage_width, 1.17)
    gabled_chamber(queen_center_y, queen_floor, queen_width_x, queen_depth_y, 3.2, 12.0 * cubit_m)

    gallery_width = 4.0 * cubit_m
    gallery_height = 8.6
    tunnel(asc_end_y, asc_end_z, gallery_end_y, gallery_end_z, gallery_width, gallery_height)

    king_floor = 43.03
    king_center_y = -2.0
    king_width_x = 20.0 * cubit_m
    king_depth_y = 10.0 * cubit_m
    king_height = 5.8
    tunnel(gallery_end_y, gallery_end_z, king_center_y + king_depth_y / 2.0, king_floor + 1.2, passage_width, 1.2)
    chamber_box(king_center_y, king_floor, king_width_x, king_depth_y, king_height)
    chamber_box(king_center_y, king_floor, 2.28, 0.98, 1.05)

    relief_z = king_floor + king_height + 0.65
    relief_height_mm = max(m(0.75), 0.5)
    relief_step_mm = max(m(1.35), 0.9)
    relief_height_m = relief_height_mm / scale
    relief_step_m = relief_step_mm / scale
    for index in range(5):
        chamber_box(king_center_y, relief_z + index * relief_step_m, king_width_x, king_depth_y, relief_height_m)
    top_relief_z = m(relief_z) + 5 * relief_step_mm
    relief_top_floor = top_relief_z / scale
    gabled_chamber(king_center_y, relief_top_floor, king_width_x, king_depth_y, (relief_height_mm * 0.6) / scale, (relief_height_mm * 1.9) / scale)

    shaft_width = 0.65
    king_shaft_z = king_floor + 0.91
    tunnel(king_center_y + king_depth_y / 2.0, king_shaft_z, surface_half_m(72.0), 72.0, shaft_width, shaft_width)
    tunnel(king_center_y - king_depth_y / 2.0, king_shaft_z, -surface_half_m(72.0), 72.0, shaft_width, shaft_width)
    queen_shaft_z = queen_floor + 2.4
    tunnel(queen_center_y + queen_depth_y / 2.0, queen_shaft_z, surface_half_m(55.0) * 0.65, 55.0, shaft_width, shaft_width)
    tunnel(queen_center_y - queen_depth_y / 2.0, queen_shaft_z, -surface_half_m(55.0) * 0.65, 55.0, shaft_width, shaft_width)

    return mesh


def make_internal_chamber_layer(p: KitParams, level: int) -> Mesh:
    return make_internal_chambers_reference(
        p,
        zmin_mm=course_z(p, level),
        zmax_mm=course_z(p, level + 1),
        name=f"internal_chambers_layer_{level + 1:02d}",
    )


def make_subterranean_chambers_reference(p: KitParams) -> Mesh:
    return make_internal_chambers_reference(
        p,
        zmin_mm=None,
        zmax_mm=0.0,
        name="internal_chambers_subterranean_precut",
    )


def combine(name: str, meshes: Iterable[Mesh]) -> Mesh:
    out = Mesh(name)
    for mesh in meshes:
        out.extend(mesh)
    return out


def mesh_stats(mesh: Mesh, rel_path: str) -> dict[str, object]:
    min_x, min_y, min_z, max_x, max_y, max_z = mesh.bounds()
    return {
        "file": rel_path,
        "triangles": len(mesh.triangles),
        "bounds_mm": {
            "min": [round(min_x, 3), round(min_y, 3), round(min_z, 3)],
            "max": [round(max_x, 3), round(max_y, 3), round(max_z, 3)],
        },
    }


def export_mesh(mesh: Mesh, path: Path, manifest: list[dict[str, object]], root: Path, printable: bool = False) -> None:
    out = mesh.print_pose() if printable else mesh
    out.write_ascii_stl(path)
    manifest.append(mesh_stats(out, str(path.relative_to(root))))


def clear_old_outputs(root: Path) -> None:
    if not root.exists():
        return
    for pattern in ("*.stl", "*.json"):
        for path in root.rglob(pattern):
            path.unlink()


def generate(p: KitParams) -> list[dict[str, object]]:
    root = p.output_dir
    clear_old_outputs(root)
    printable = root / "printable"
    core_layers_dir = printable / "core_layers"
    ramp_segments_dir = printable / "ramp_segments"
    fill_layers_dir = printable / "fill_layers"
    ramp_layers_dir = printable / "ramp_layers"
    chamber_layers_dir = printable / "chamber_layers"
    view = root / "view_stages"
    constructed = root / "constructed_states"
    demo_parts = root / "demo_parts"
    demo_core_layers = root / "demo_layers" / "core"
    demo_fill_layers = root / "demo_layers" / "fill"
    demo_ramp_layers = root / "demo_layers" / "ramps"
    demo_chamber_layers = root / "demo_layers" / "chambers"

    manifest: list[dict[str, object]] = []
    core = make_stepped_core(p)
    display_core = make_display_stepped_core(p)
    full_backfill = make_temporary_backfill(p)
    cut_backfill = make_cut_temporary_backfill(p)
    ramps_all, ramp_faces, ramp_segments = make_ramps(p)
    ramp_underfill_all, ramp_underfill_faces = make_ramp_underfill(p)
    supported_ramps_all = combine("temporary_switchback_ramps_all_sides_local_underfill", [ramp_underfill_all, ramps_all])
    platform = make_platform(p)
    capstone = make_capstone(p)
    finished_surface = make_finished_pyramid_surface(p)
    chambers = make_internal_chambers_reference(p)
    subterranean_chambers = make_subterranean_chambers_reference(p)
    casing_rings = [make_casing_ring(p, i) for i in range(p.casing_rings)]
    display_casing_rings = [make_casing_ring(p, i, include_caps=False) for i in range(p.casing_rings)]
    reuse_stockpile = make_reuse_stockpile(p)
    next_seed = make_next_foundation_seed(p)

    export_mesh(core, printable / "inner_stepped_core.stl", manifest, root, printable=True)
    export_mesh(cut_backfill, printable / "temporary_ramp_backfill.stl", manifest, root, printable=True)
    export_mesh(full_backfill, printable / "temporary_full_stepped_mound_reference.stl", manifest, root, printable=True)
    export_mesh(ramp_underfill_all, printable / "temporary_ramp_local_underfill.stl", manifest, root, printable=True)
    export_mesh(supported_ramps_all, printable / "temporary_switchback_ramps_all_sides.stl", manifest, root, printable=True)
    for face_name, face_mesh in ramp_faces.items():
        local_underfill = ramp_underfill_faces.get(face_name)
        parts = [local_underfill, face_mesh] if local_underfill is not None else [face_mesh]
        export_mesh(combine(f"temporary_switchback_ramps_{face_name}_local_underfill", parts), printable / f"temporary_switchback_ramps_{face_name}.stl", manifest, root, printable=True)
    for name, segment in ramp_segments.items():
        export_mesh(segment, ramp_segments_dir / f"{name}.stl", manifest, root, printable=True)
    export_mesh(platform, printable / "temporary_flat_capstone_platform.stl", manifest, root, printable=True)
    export_mesh(capstone, printable / "capstone.stl", manifest, root, printable=True)
    export_mesh(chambers, printable / "internal_chambers_reference.stl", manifest, root, printable=True)
    export_mesh(subterranean_chambers, printable / "internal_chambers_subterranean_precut.stl", manifest, root, printable=True)
    export_mesh(reuse_stockpile, printable / "reuse_material_stockpile_for_next_pyramid.stl", manifest, root, printable=True)
    export_mesh(next_seed, printable / "next_pyramid_seed_foundation.stl", manifest, root, printable=True)

    for top_order, ring in enumerate(reversed(casing_rings), start=1):
        export_mesh(ring, printable / f"casing_ring_top_{top_order:02d}.stl", manifest, root, printable=True)

    for level in range(p.courses):
        core_layer = make_stepped_core_layer(p, level)
        fill_layer = make_cut_temporary_backfill_layer(p, level)
        ramp_layer = make_ramp_layer(p, level)
        chamber_layer = make_internal_chamber_layer(p, level)
        export_mesh(core_layer, core_layers_dir / f"inner_mound_layer_{level + 1:02d}.stl", manifest, root, printable=True)
        export_mesh(fill_layer, fill_layers_dir / f"temporary_fill_layer_{level + 1:02d}.stl", manifest, root, printable=True)
        export_mesh(ramp_layer, ramp_layers_dir / f"temporary_ramp_layer_{level + 1:02d}.stl", manifest, root, printable=True)
        export_mesh(chamber_layer, chamber_layers_dir / f"internal_chamber_layer_{level + 1:02d}.stl", manifest, root, printable=True)
        export_mesh(core_layer, demo_core_layers / f"core_layer_{level + 1:02d}.stl", manifest, root, printable=False)
        export_mesh(fill_layer, demo_fill_layers / f"fill_layer_{level + 1:02d}.stl", manifest, root, printable=False)
        export_mesh(ramp_layer, demo_ramp_layers / f"ramp_layer_{level + 1:02d}.stl", manifest, root, printable=False)
        export_mesh(chamber_layer, demo_chamber_layers / f"chamber_layer_{level + 1:02d}.stl", manifest, root, printable=False)

    export_mesh(core, demo_parts / "inner_stepped_core.stl", manifest, root, printable=False)
    export_mesh(cut_backfill, demo_parts / "temporary_cut_stepped_mound.stl", manifest, root, printable=False)
    export_mesh(ramp_underfill_all, demo_parts / "temporary_ramp_local_underfill.stl", manifest, root, printable=False)
    export_mesh(supported_ramps_all, demo_parts / "temporary_switchback_ramps_all_sides.stl", manifest, root, printable=False)
    export_mesh(platform, demo_parts / "temporary_flat_capstone_platform.stl", manifest, root, printable=False)
    export_mesh(capstone, demo_parts / "capstone.stl", manifest, root, printable=False)
    export_mesh(chambers, demo_parts / "internal_chambers_reference.stl", manifest, root, printable=False)
    export_mesh(subterranean_chambers, demo_parts / "internal_chambers_subterranean_precut.stl", manifest, root, printable=False)
    export_mesh(reuse_stockpile, demo_parts / "reuse_material_stockpile_for_next_pyramid.stl", manifest, root, printable=False)
    export_mesh(next_seed, demo_parts / "next_pyramid_seed_foundation.stl", manifest, root, printable=False)
    for top_order, ring in enumerate(reversed(display_casing_rings), start=1):
        export_mesh(ring, demo_parts / f"casing_ring_top_{top_order:02d}.stl", manifest, root, printable=False)

    top_threshold = p.core_height_mm * 0.62
    mid_threshold = p.core_height_mm * 0.28
    top_remaining_backfill = make_cut_temporary_backfill(p, max_z=top_threshold)
    mid_remaining_backfill = make_cut_temporary_backfill(p, max_z=mid_threshold)
    top_remaining_underfill, _ = make_ramp_underfill(p, max_z=top_threshold)
    mid_remaining_underfill, _ = make_ramp_underfill(p, max_z=mid_threshold)
    top_remaining_ramps, _, _ = make_ramps(p, max_z=top_threshold)
    mid_remaining_ramps, _, _ = make_ramps(p, max_z=mid_threshold)
    top_supported_ramps = combine("top_remaining_local_underfilled_ramps", [top_remaining_underfill, top_remaining_ramps])
    mid_supported_ramps = combine("mid_remaining_local_underfilled_ramps", [mid_remaining_underfill, mid_remaining_ramps])
    staged_display_casing = display_casing_rings[:-1]
    upper_casing = [ring for i, ring in enumerate(staged_display_casing) if (i / p.casing_rings) >= 0.62]
    mid_casing = [ring for i, ring in enumerate(staged_display_casing) if (i / p.casing_rings) >= 0.28]

    stages = [
        (
            "stage_01_inner_core_with_temporary_switchback_ramps.stl",
            combine("stage_01_cut_mound_single_switchback_ramps", [cut_backfill, supported_ramps_all]),
        ),
        (
            "stage_02_capstone_on_flat_platform_before_deramping.stl",
            combine("stage_02_capstone_platform", [cut_backfill, supported_ramps_all, platform, capstone]),
        ),
        (
            "stage_03_upper_ramps_removed_top_casing_added.stl",
            combine("stage_03_top_down_deramping", [display_core, top_remaining_backfill, top_supported_ramps, capstone, *upper_casing]),
        ),
        (
            "stage_04_lower_ramps_remaining_more_casing_added.stl",
            combine("stage_04_more_casing", [display_core, mid_remaining_backfill, mid_supported_ramps, capstone, *mid_casing]),
        ),
        (
            "stage_05_finished_pyramid_core_casing_capstone.stl",
            finished_surface,
        ),
        (
            "stage_06_finished_pyramid_with_reuse_material_for_next_one.stl",
            combine("stage_06_reuse_material", [finished_surface, reuse_stockpile, next_seed]),
        ),
    ]
    for filename, stage in stages:
        export_mesh(stage, view / filename, manifest, root, printable=False)

    constructed_states = [
        (
            "constructed_01_full_backfilled_ramp_system.stl",
            combine("constructed_01_full_supported_ramp_system", [cut_backfill, supported_ramps_all]),
        ),
        (
            "constructed_02_capstone_set_before_deramping.stl",
            combine("constructed_02_capstone_set_before_deramping", [cut_backfill, supported_ramps_all, platform, capstone]),
        ),
        (
            "constructed_03_partial_top_down_deramping.stl",
            combine("constructed_03_partial_top_down_deramping", [display_core, top_remaining_backfill, top_supported_ramps, capstone, *upper_casing]),
        ),
        (
            "constructed_04_finished_pyramid.stl",
            finished_surface,
        ),
    ]
    for filename, state in constructed_states:
        export_mesh(state, constructed / filename, manifest, root, printable=False)

    manifest_doc = {
        "description": "Parametric STL kit for a conceptual inner-core, switchback-ramp, top-down casing construction sequence.",
        "units": "millimeters",
        "parameters": {
            "base_mm": p.base_mm,
            "height_mm": p.height_mm,
            "capstone_height_mm": p.capstone_height_mm,
            "courses": p.courses,
            "casing_rings": p.casing_rings,
            "core_base_fraction": p.core_base_fraction,
            "core_top_fraction": p.core_top_fraction,
            "ramp_width_mm": p.ramp_width_mm,
            "ramp_gap_mm": p.ramp_gap_mm,
            "ramp_margin_mm": p.ramp_margin_mm,
            "ramp_platform_fraction": p.ramp_platform_fraction,
            "landing_corner_notch_fraction": p.landing_corner_notch_fraction,
            "top_platform_half_fraction": p.top_platform_half_fraction,
            "temporary_overbuild_mm": p.temporary_overbuild_mm,
            "computed_temporary_overbuild_mm": round(temporary_overbuild_offset(p), 3),
        },
        "files": manifest,
    }
    (root / "manifest.json").write_text(json.dumps(manifest_doc, indent=2), encoding="utf-8")
    return manifest


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the Giza construction theory STL kit.")
    parser.add_argument("--output-dir", default="dist", type=Path, help="Directory for generated STL files.")
    parser.add_argument("--base-mm", default=160.0, type=float, help="Finished pyramid base width in mm.")
    parser.add_argument("--height-mm", default=101.8, type=float, help="Finished pyramid height in mm.")
    parser.add_argument("--capstone-height-mm", default=7.0, type=float, help="Height of the removable capstone/pyramidion.")
    parser.add_argument("--courses", default=16, type=int, help="Number of stepped core courses and ramp switchbacks.")
    parser.add_argument("--casing-rings", default=16, type=int, help="Number of removable casing rings.")
    parser.add_argument("--ramp-width-mm", default=18.0, type=float, help="Temporary ramp ribbon width.")
    parser.add_argument("--ramp-gap-mm", default=4.0, type=float, help="Gap between temporary work deck/face and ramp ribbon.")
    parser.add_argument("--top-platform-half-fraction", default=0.24, type=float, help="Temporary top work-deck half-width as a fraction of finished base width.")
    parser.add_argument("--temporary-overbuild-mm", default=0.0, type=float, help="Uniform outward offset for the temporary overbuilt work mass. Default 0 infers it from the top deck size.")
    parser.add_argument("--core-base-fraction", default=0.65, type=float, help="Inner core base half-width as fraction of final half-width.")
    parser.add_argument("--core-top-fraction", default=0.62, type=float, help="Inner core top half-width as fraction of capstone base half-width.")
    return parser


def params_from_args(args: argparse.Namespace) -> KitParams:
    if args.courses < 4:
        raise SystemExit("--courses must be at least 4")
    if args.casing_rings < 2:
        raise SystemExit("--casing-rings must be at least 2")
    if args.height_mm <= args.capstone_height_mm:
        raise SystemExit("--height-mm must be greater than --capstone-height-mm")
    return KitParams(
        base_mm=args.base_mm,
        height_mm=args.height_mm,
        capstone_height_mm=args.capstone_height_mm,
        courses=args.courses,
        casing_rings=args.casing_rings,
        ramp_width_mm=args.ramp_width_mm,
        ramp_gap_mm=args.ramp_gap_mm,
        top_platform_half_fraction=args.top_platform_half_fraction,
        temporary_overbuild_mm=args.temporary_overbuild_mm,
        core_base_fraction=args.core_base_fraction,
        core_top_fraction=args.core_top_fraction,
        output_dir=args.output_dir,
    )


def main() -> None:
    args = build_arg_parser().parse_args()
    params = params_from_args(args)
    manifest = generate(params)
    stl_count = sum(1 for item in manifest if str(item["file"]).endswith(".stl"))
    print(f"Generated {stl_count} STL files in {params.output_dir}")
    print(f"Finished pyramid: {params.base_mm:.1f} mm base x {params.height_mm:.1f} mm high")
    print(f"Core/ramp courses: {params.courses}, removable casing rings: {params.casing_rings}")


if __name__ == "__main__":
    main()
