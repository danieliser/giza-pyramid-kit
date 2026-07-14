# Giza Pyramid Construction Theory STL Kit

## Short Summary

A printable, modular model of a top-down Giza pyramid construction hypothesis: stepped inner mound, single-switchback ramps, broad capstone platform, top-down deramping, removable casing rings, chamber references, and reuse material for the next pyramid.

## Description

This STL kit turns a construction theory into something you can print, assemble, and take apart.

The concept modeled here is not the spiral-ramp theory. It follows the Huni Choi / DamiLee-style top-down idea: first build an oversized stepped working mass with switchback ramps and a broad flat top platform, place a small pyramidion/capstone, then remove the temporary ramp and fill material from the top down while adding the final casing stones. The removed stone is represented as stock for the next pyramid/foundation.

This is a conceptual/educational geometry model, not archaeological proof. The point is to make the construction sequence inspectable: access paths, landings, top platform, casing order, chamber references, and material reuse all become physical parts instead of only a diagram.

## What Is Included

The upload bundle includes:

- `STL/constructed_states/` - four single-piece snapshots of the sequence
- `STL/view_stages/` - six assembled view stages
- `STL/printable/` - printable kit pieces
- `STL/printable/core_layers/` - 16 inner mound layers
- `STL/printable/fill_layers/` - 16 temporary fill layers
- `STL/printable/ramp_layers/` - 16 ramp/landing/support layers
- `STL/printable/chamber_layers/` - chamber reference slices by course
- `STL/printable/ramp_segments/` - per-face, per-level modular ramp pieces
- `images/` - preview renders for the listing
- `PRINTING.md` - scale and slicer notes
- `manifest.json` - generated file list with dimensions and triangle counts

## Suggested First Prints

For a quick visual release print:

1. Print `STL/constructed_states/constructed_01_full_backfilled_ramp_system.stl`
2. Print `STL/constructed_states/constructed_02_capstone_set_before_deramping.stl`
3. Print `STL/constructed_states/constructed_03_partial_top_down_deramping.stl`
4. Print `STL/constructed_states/constructed_04_finished_pyramid.stl`

For a more interactive kit:

1. Print `STL/printable/inner_stepped_core.stl`
2. Print `STL/printable/temporary_ramp_backfill.stl`
3. Print `STL/printable/temporary_ramp_local_underfill.stl`
4. Print `STL/printable/temporary_switchback_ramps_all_sides.stl`
5. Print `STL/printable/temporary_flat_capstone_platform.stl`
6. Print `STL/printable/capstone.stl`
7. Print `STL/printable/casing_ring_top_01.stl` through `casing_ring_top_16.stl`
8. Optionally print `internal_chambers_reference.stl`, the chamber layer files, and the reuse stockpile pieces

## Print Settings

- Material: PLA
- Nozzle: 0.4 mm
- Layer height: 0.12-0.20 mm
- Walls/perimeters: 2-3
- Infill: 10-15% is enough for most pieces
- Supports: usually off; the ramp files include local underfill
- Bed adhesion: brim recommended for the capstone, chamber references, and small modular ramp segments

The default finished pyramid is `160 x 160 x 101.8 mm`. The full temporary ramp state is about `265 x 265 mm`, so it is too large for many beds as a single piece.

For a Flashforge Adventurer 4 Pro:

- `62.5%` scale is the recommended modular filming size
- `75%` fits nominally but leaves almost no margin on the 200 mm bed axis
- `50%` is close to the practical lower limit with a 0.4 mm nozzle

The modular stackable pieces include `0.35 mm` XY clearance by default around the core/fill and fill/ramp-support interfaces. If your printer tends to make tight assemblies, regenerate the kit with `--stack-clearance-mm 0.5`.

If you scale the supplied STLs in the slicer, that clearance scales down too. For the best modular fit at smaller sizes, regenerate the kit at the target dimensions and keep `--stack-clearance-mm` at `0.35` or higher.

## Notes

The chamber pieces are schematic references, not survey-grade voids. They are meant to help show where the known internal route could sit relative to the course-by-course build.

The included Python generator can regenerate the full STL set with different base sizes, course counts, ramp widths, and capstone size.

## Links

- GitHub project: [danieliser/giza-pyramid-kit](https://github.com/danieliser/giza-pyramid-kit)
- Animated demo: [open the browser demo](https://danieliser.github.io/giza-pyramid-kit/demo/)

## Tags

giza, pyramid, egypt, archaeology, construction, educational, stl, 3d-printing, ramps, capstone, modular, model, diorama, history, geometry

## Category

3D Printing > Models / Education / Architecture

## Suggested License Selection

Maker-site license: Creative Commons Attribution-NonCommercial-ShareAlike 4.0.

The software source in the GitHub repository is separately licensed under MIT.
