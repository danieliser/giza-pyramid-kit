#!/usr/bin/env python3
"""Lightweight geometry checks for the generated Giza STL kit."""

from __future__ import annotations

from collections import Counter

from generate_giza_kit import (
    KitParams,
    combine,
    core_cut_rect_for_level,
    core_half_at_fraction,
    course_z,
    make_capstone,
    make_casing_ring,
    make_display_core_below_capstone,
    make_internal_chamber_layer,
    make_cut_temporary_backfill_layer,
    make_cut_temporary_backfill,
    make_corner_ramp_underfill,
    make_corner_landing,
    make_internal_chambers_reference,
    make_ramp_layer,
    make_ramp_underfill_layer,
    make_ramp_underfill,
    make_ramp_segment,
    make_side_ramp_underfill_layer,
    make_stepped_core,
    make_stepped_core_layer,
    make_subterranean_chambers_reference,
    make_temporary_backfill,
    normal,
    ramp_floor_z,
    ramp_lane_bounds,
    ramp_lane_count,
    ramp_level_count,
    ramp_top_z,
    ramp_underfill_cut_rects,
    temporary_fill_cut_rects,
)


EPS = 0.001


def signed_volume(mesh) -> float:
    volume = 0.0
    for a, b, c in mesh.triangles:
        volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6.0
    return volume


def nonmanifold_edge_count(mesh) -> int:
    edges: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = Counter()

    def vertex_key(vertex):
        return tuple(round(value, 5) for value in vertex)

    def edge_key(a, b):
        return tuple(sorted((vertex_key(a), vertex_key(b))))

    for a, b, c in mesh.triangles:
        edges[edge_key(a, b)] += 1
        edges[edge_key(b, c)] += 1
        edges[edge_key(c, a)] += 1
    return sum(1 for count in edges.values() if count != 2)


def triangle_centroid_xy(triangle) -> tuple[float, float]:
    return (
        (triangle[0][0] + triangle[1][0] + triangle[2][0]) / 3.0,
        (triangle[0][1] + triangle[1][1] + triangle[2][1]) / 3.0,
    )


def point_strictly_inside_rect(x: float, y: float, rect, eps: float = EPS) -> bool:
    xmin, xmax, ymin, ymax = rect
    return xmin + eps < x < xmax - eps and ymin + eps < y < ymax - eps


def require_closed_positive(errors: list[str], label: str, mesh, allow_empty: bool = False) -> None:
    if not mesh.triangles:
        if not allow_empty:
            errors.append(f"{label}: mesh is empty")
        return
    if signed_volume(mesh) <= 0:
        errors.append(f"{label}: signed volume is not positive")
    open_edges = nonmanifold_edge_count(mesh)
    if open_edges:
        errors.append(f"{label}: {open_edges} non-manifold edges")


def require_z_bounds(errors: list[str], label: str, mesh, expected_min: float | None, expected_max: float | None) -> None:
    if not mesh.triangles:
        return
    _, _, min_z, _, _, max_z = mesh.bounds()
    if expected_min is not None and abs(min_z - expected_min) > EPS:
        errors.append(f"{label}: min z {min_z:.3f} does not match expected {expected_min:.3f}")
    if expected_max is not None and abs(max_z - expected_max) > EPS:
        errors.append(f"{label}: max z {max_z:.3f} does not match expected {expected_max:.3f}")


def require_no_centroids_in_cutouts(errors: list[str], label: str, mesh, cut_rects) -> None:
    for index, triangle in enumerate(mesh.triangles):
        x, y = triangle_centroid_xy(triangle)
        if any(point_strictly_inside_rect(x, y, rect) for rect in cut_rects):
            errors.append(f"{label}: triangle {index} intrudes into a reserved cutout")
            return


def validate_stack_clearances(params: KitParams) -> list[str]:
    errors: list[str] = []
    for level in range(ramp_level_count(params)):
        core_half = core_half_at_fraction(params, level / params.courses)
        _, cut_half, _, _ = core_cut_rect_for_level(params, level)
        clearance = cut_half - core_half
        if clearance < params.stack_clearance_mm - EPS:
            errors.append(
                f"level {level + 1}: core-to-fill clearance {clearance:.3f} mm is below requested "
                f"{params.stack_clearance_mm:.3f} mm"
            )
        if level > 0:
            inner, _ = ramp_lane_bounds(params, level, 0)
            central_cut = ramp_underfill_cut_rects(params, level)[0]
            inner_clearance = central_cut[1] - inner
            if inner_clearance < params.stack_clearance_mm - EPS:
                errors.append(
                    f"level {level + 1}: fill-to-ramp-support clearance {inner_clearance:.3f} mm is below requested "
                    f"{params.stack_clearance_mm:.3f} mm"
                )
    return errors


def validate_ramps() -> list[str]:
    params = KitParams()
    errors: list[str] = validate_stack_clearances(params)
    require_closed_positive(errors, "inner mound core", make_stepped_core(params))
    for level in range(ramp_level_count(params)):
        expected_floor = ramp_floor_z(params, level)
        for lane in range(ramp_lane_count()):
            lane_inner, lane_outer = ramp_lane_bounds(params, level, lane)
            if lane_outer <= lane_inner:
                errors.append(f"level {level + 1}, lane {lane + 1}: ramp lane has non-positive width")
            for face in range(4):
                mesh = make_ramp_segment(params, face, level, lane)
                volume = signed_volume(mesh)
                min_z = mesh.bounds()[2]
                normals = [normal(*tri) for tri in mesh.triangles]
                sloped_up = [n for n in normals if n[2] > 0.05 and abs(n[0]) + abs(n[1]) > 0.01]
                open_edges = nonmanifold_edge_count(mesh)
                if volume <= 0:
                    errors.append(f"face {face + 1}, level {level + 1}, lane {lane + 1}: signed volume is not positive")
                if open_edges:
                    errors.append(f"face {face + 1}, level {level + 1}, lane {lane + 1}: {open_edges} non-manifold edges")
                if abs(min_z - expected_floor) > 0.001:
                    errors.append(
                        f"face {face + 1}, level {level + 1}, lane {lane + 1}: ramp bottom {min_z:.3f} is not at expected support {expected_floor:.3f}"
                    )
                if len(sloped_up) < 2:
                    errors.append(f"face {face + 1}, level {level + 1}, lane {lane + 1}: sloped walking surface is not upward-facing")
            for corner in ("ne", "se", "sw", "nw"):
                landing = make_corner_landing(params, corner, level, lane)
                if not landing.triangles:
                    continue
                min_z = landing.bounds()[2]
                open_edges = nonmanifold_edge_count(landing)
                if signed_volume(landing) <= 0:
                    errors.append(f"corner {corner}, level {level + 1}, lane {lane + 1}: signed volume is not positive")
                if open_edges:
                    errors.append(f"corner {corner}, level {level + 1}, lane {lane + 1}: {open_edges} non-manifold edges")
                if abs(min_z - expected_floor) > 0.001:
                    errors.append(
                        f"corner {corner}, level {level + 1}, lane {lane + 1}: landing bottom {min_z:.3f} is not at expected support {expected_floor:.3f}"
                    )
        if level > 0:
            underfill_layer = make_ramp_underfill_layer(params, level)
            require_closed_positive(errors, f"ramp support layer {level + 1}", underfill_layer)
            require_z_bounds(
                errors,
                f"ramp support layer {level + 1}",
                underfill_layer,
                course_z(params, level - 1),
                expected_floor,
            )
            require_no_centroids_in_cutouts(errors, f"ramp support layer {level + 1}", underfill_layer, ramp_underfill_cut_rects(params, level))
            for face in range(4):
                side_fill = make_side_ramp_underfill_layer(params, face, level)
                require_closed_positive(errors, f"side ramp support face {face + 1}, level {level + 1}", side_fill)
                require_z_bounds(
                    errors,
                    f"side ramp support face {face + 1}, level {level + 1}",
                    side_fill,
                    course_z(params, level - 1),
                    expected_floor,
                )
            for corner in ("ne", "se", "sw", "nw"):
                corner_fill = make_corner_ramp_underfill(params, corner, level)
                require_closed_positive(errors, f"corner ramp support {corner}, level {level + 1}", corner_fill)
                require_z_bounds(
                    errors,
                    f"corner ramp support {corner}, level {level + 1}",
                    corner_fill,
                    course_z(params, level - 1),
                    expected_floor,
                )
    backfill = make_temporary_backfill(params)
    require_closed_positive(errors, "temporary full backfill reference", backfill)
    cut_backfill = make_cut_temporary_backfill(params)
    require_closed_positive(errors, "cut temporary backfill", cut_backfill)
    ramp_underfill, _ = make_ramp_underfill(params)
    require_closed_positive(errors, "local ramp underfill", ramp_underfill)
    chambers = make_internal_chambers_reference(params)
    if not chambers.triangles:
        errors.append("internal chamber reference mesh is empty")
    elif signed_volume(chambers) <= 0:
        errors.append("internal chamber reference signed volume is not positive")
    subterranean = make_subterranean_chambers_reference(params)
    if not subterranean.triangles:
        errors.append("subterranean chamber precut mesh is empty")
    elif signed_volume(subterranean) <= 0:
        errors.append("subterranean chamber precut signed volume is not positive")
    elif subterranean.bounds()[5] > EPS:
        errors.append(f"subterranean chamber precut rises above ground plane: max z {subterranean.bounds()[5]:.3f}")
    for level in range(ramp_level_count(params)):
        core_layer = make_stepped_core_layer(params, level)
        require_closed_positive(errors, f"inner mound layer {level + 1}", core_layer)
        require_z_bounds(errors, f"inner mound layer {level + 1}", core_layer, course_z(params, level), course_z(params, level + 1))
        fill_layer = make_cut_temporary_backfill_layer(params, level)
        require_closed_positive(errors, f"cut fill layer {level + 1}", fill_layer)
        require_z_bounds(errors, f"cut fill layer {level + 1}", fill_layer, course_z(params, level), course_z(params, level + 1))
        require_no_centroids_in_cutouts(errors, f"cut fill layer {level + 1}", fill_layer, temporary_fill_cut_rects(params, level))
        require_no_centroids_in_cutouts(errors, f"cut fill layer {level + 1}", fill_layer, [core_cut_rect_for_level(params, level)])
        ramp_layer = make_ramp_layer(params, level)
        if ramp_layer.triangles and signed_volume(ramp_layer) <= 0:
            errors.append(f"ramp layer {level + 1}: signed volume is not positive")
        chamber_layer = make_internal_chamber_layer(params, level)
        if chamber_layer.triangles and signed_volume(chamber_layer) <= 0:
            errors.append(f"internal chamber layer {level + 1}: signed volume is not positive")
        if chamber_layer.triangles:
            min_z = chamber_layer.bounds()[2]
            max_z = chamber_layer.bounds()[5]
            if min_z < course_z(params, level) - EPS or max_z > course_z(params, level + 1) + EPS:
                errors.append(
                    f"internal chamber layer {level + 1}: z bounds {min_z:.3f}..{max_z:.3f} escape course "
                    f"{course_z(params, level):.3f}..{course_z(params, level + 1):.3f}"
                )
    return errors


def validate_capstone_transition() -> list[str]:
    params = KitParams()
    errors: list[str] = []
    display_top = combine(
        "capstone_transition_check",
        [
            make_display_core_below_capstone(params),
            make_casing_ring(params, params.casing_rings - 1, include_caps=False),
            make_capstone(params),
        ],
    )
    cap_base_z = params.core_height_mm
    cap_half = params.capstone_base_half_mm
    stray_vertices = 0
    for tri in display_top.triangles:
        for x, y, z in tri:
            if abs(z - cap_base_z) <= 0.001 and max(abs(x), abs(y)) > cap_half + 0.01:
                stray_vertices += 1
    if stray_vertices:
        errors.append(f"capstone transition has {stray_vertices} vertices forming a shelf outside the capstone footprint")
    return errors


def main() -> None:
    errors = [*validate_ramps(), *validate_capstone_transition()]
    if errors:
        print("Geometry validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("Geometry validation passed: single switchback ramps, notched landings, cut mound, local underfill, chamber reference, and capstone transition are clean.")


if __name__ == "__main__":
    main()
