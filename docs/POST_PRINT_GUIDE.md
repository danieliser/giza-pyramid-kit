# First Print And Post-Print Launch Guide

The first physical build has two jobs: confirm that the removable geometry works,
and produce honest photos and video for the public release. Do not start by printing
every optional chamber or stockpile piece. Prove the stack first.

## Recommended MVP

For the actual build-and-deramp video, print the modular kit at `62.5%` scale:

- `dist/printable/core_layers/inner_mound_layer_01.stl` through `16.stl`
- `dist/printable/fill_layers/temporary_fill_layer_01.stl` through `16.stl`
- `dist/printable/ramp_layers/temporary_ramp_layer_01.stl` through `16.stl`
- `dist/printable/casing_ring_top_01.stl` through `top_16.stl`
- `dist/printable/temporary_flat_capstone_platform.stl`
- `dist/printable/capstone.stl`

Leave the chamber slices, reuse pile, and next-pyramid foundation for a second pass.
They improve the explanation, but they are not required to prove the motion.

The supplied STL clearance scales with the model. At `62.5%`, the default `0.35 mm`
clearance becomes about `0.22 mm`. Print the fit test below before committing to the
whole kit. If it binds, regenerate at the target dimensions with at least `0.4-0.5 mm`
clearance instead of forcing the parts.

## Planning Estimates

These are planning ranges, not slicer promises. They are derived from the generated
mesh volumes, scaled geometrically, then adjusted for thin course slabs, two walls,
three top/bottom layers, and `10%` infill. FlashPrint's estimate after slicing is the
number to record on print day.

| Plan | Scale | Estimated time | PLA | Purpose |
| --- | ---: | ---: | ---: | --- |
| Static proof pair: capstone state + finished pyramid | `50%` | `18-28 h` | `300-400 g` | Fastest credible before/after photos |
| Static proof trio: add partial deramping state | `50%` | `30-44 h` | `500-700 g` | Three physical storyboard frames |
| Modular teardown kit | `50%` | `28-40 h` | `350-500 g` | Fast but delicate working model |
| Modular teardown kit | `62.5%` | `45-65 h` | `600-900 g` | Recommended filming model |
| Modular teardown kit | `75%` | `70-100 h` | `0.9-1.3 kg` | Better detail, poor bed margin |

The Adventurer 4 Pro build volume is `220 x 200 x 250 mm`. A `75%` temporary state
is about `199 x 199 mm`, leaving almost no usable margin on the 200 mm axis. Use
`62.5%` for the first complete filming kit and keep a full 1 kg spool available.

## Fit Test First

Before the long run, print this lower-course sample at the intended scale and settings:

1. `core_layers/inner_mound_layer_01.stl` through `03.stl`
2. `fill_layers/temporary_fill_layer_01.stl` through `03.stl`
3. `ramp_layers/temporary_ramp_layer_01.stl` through `03.stl`
4. `casing_ring_top_16.stl`, `top_15.stl`, and `top_14.stl`
5. `temporary_flat_capstone_platform.stl` and `capstone.stl`

Check that the pieces sit flat without pressure, the ramps do not rock, and the casing
rings can replace removed temporary layers. A light deburr is normal. Sanding every
interface until it fits is a failed clearance test.

## Starting Slicer Profile

- Printer: Flashforge Adventurer 4 Pro
- Material: PLA
- Nozzle: `0.4 mm`
- Layer height: `0.20 mm`; use `0.16 mm` for capstone and chamber references
- Walls: `2`
- Top/bottom layers: `3`
- Infill: `10%` grid or gyroid
- Supports: off
- First-layer speed: `20-30 mm/s`
- General speed: `80-120 mm/s`, depending on the nozzle profile and filament
- Brim: capstone and chamber pieces only unless a larger layer starts lifting

Avoid placing the largest lower layers at the extreme edge of the bed. Keep the PEI
sheet clean, remove any first-layer lip before fit testing, and do not glue parts that
must move during filming.

## Color Plan

Separate colors make the construction sequence readable without labels:

- Permanent inner mound: muted stone or gray
- Temporary fill and ramps: ochre or warm brown
- Final casing rings: pale limestone or ivory
- Capstone: gold or contrasting yellow
- Optional chamber references: charcoal or dark blue

Print by material role rather than by assembly order. Label the underside of every
layer with its course number as it leaves the bed.

## Assembly And Cleanup

1. Remove brims and first-layer flare with a deburring tool or fine sanding block.
2. Dry-stack all core layers and confirm that the tower remains square.
3. Add fill and ramp layers from course 1 upward.
4. Set the temporary platform and capstone.
5. Remove temporary layers from course 16 downward.
6. Add `casing_ring_top_01` first, then continue downward through `top_16`.
7. Stop and photograph any collision, rocking part, or unexpected gap before correcting it.

The failure photos matter. They distinguish a tested model from a polished render.

## Film The Sequence

Lock the camera and model position before moving any pieces. Record both landscape
and vertical framing if possible.

Capture these shots:

1. Empty base and lower-course fit test
2. Course-by-course core, fill, and ramp buildup
3. Small capstone on the broad working deck
4. Top-down removal with casing replacing each cleared course
5. Optional chamber cutaway
6. Finished pyramid beside the removed temporary pieces
7. One slow hand rotation of the finished model

For stop motion, take one frame after every layer change. For live action, remove one
course at a time and pause before the next move. Do not reverse footage to fake the
mechanical sequence; the point is to show that the pieces really fit.

## Record The Actual Print

Add the measured results here after the first run:

| Field | Result |
| --- | --- |
| Scale and generated base size | |
| FlashPrint version/profile | |
| Slicer estimate | |
| Actual elapsed print time | |
| Estimated/actual filament | |
| PLA brand and color | |
| Clearance used | |
| Failed or repeated plates | |
| Tightest interface | |
| Loosest interface | |

Once those values and real photos exist, replace planning ranges in `PRINTING.md`,
replace maker-site renders where possible, and publish the first-print results as a
follow-up to the theory article.
