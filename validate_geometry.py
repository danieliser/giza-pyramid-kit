#!/usr/bin/env python3
"""Lightweight geometry checks for the generated Giza STL kit."""

from __future__ import annotations

from collections import Counter

from generate_giza_kit import (
    KitParams,
    combine,
    make_capstone,
    make_casing_ring,
    make_display_core_below_capstone,
    make_internal_chamber_layer,
    make_cut_temporary_backfill_layer,
    make_cut_temporary_backfill,
    make_corner_landing,
    make_internal_chambers_reference,
    make_ramp_layer,
    make_ramp_underfill,
    make_ramp_segment,
    make_stepped_core_layer,
    make_subterranean_chambers_reference,
    make_temporary_backfill,
    normal,
    ramp_floor_z,
    ramp_lane_bounds,
    ramp_lane_count,
    ramp_level_count,
)


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


def validate_ramps() -> list[str]:
    params = KitParams()
    errors: list[str] = []
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
    backfill = make_temporary_backfill(params)
    if signed_volume(backfill) <= 0:
        errors.append("temporary full backfill reference signed volume is not positive")
    cut_backfill = make_cut_temporary_backfill(params)
    if signed_volume(cut_backfill) <= 0:
        errors.append("cut temporary backfill signed volume is not positive")
    ramp_underfill, _ = make_ramp_underfill(params)
    if signed_volume(ramp_underfill) <= 0:
        errors.append("local ramp underfill signed volume is not positive")
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
    for level in range(ramp_level_count(params)):
        core_layer = make_stepped_core_layer(params, level)
        if core_layer.triangles and signed_volume(core_layer) <= 0:
            errors.append(f"inner mound layer {level + 1}: signed volume is not positive")
        fill_layer = make_cut_temporary_backfill_layer(params, level)
        if fill_layer.triangles and signed_volume(fill_layer) <= 0:
            errors.append(f"cut fill layer {level + 1}: signed volume is not positive")
        ramp_layer = make_ramp_layer(params, level)
        if ramp_layer.triangles and signed_volume(ramp_layer) <= 0:
            errors.append(f"ramp layer {level + 1}: signed volume is not positive")
        chamber_layer = make_internal_chamber_layer(params, level)
        if chamber_layer.triangles and signed_volume(chamber_layer) <= 0:
            errors.append(f"internal chamber layer {level + 1}: signed volume is not positive")
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
