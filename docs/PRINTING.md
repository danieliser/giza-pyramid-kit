# Printing Notes

The default kit is sized for millimeters:

- Finished pyramid body: `160 x 160 x 101.8 mm`
- Full temporary ramp/fill state: about `265 x 265 x 102 mm`
- Course height: `5.925 mm`
- Ramp width: `18 mm`
- Minimum casing wall: `1.2 mm`
- Temporary top platform thickness: `0.9 mm`
- Stackable-part XY clearance: `0.35 mm`

## Flashforge Adventurer 4 Pro

The Adventurer 4 Pro's build volume is large enough for the finished pyramid at full size, but not for the full all-sides temporary ramp state as one piece. With the default `0.4 mm` nozzle, the practical small-scale limit is set by casing walls, thin platforms, and chamber/corridor reference pieces.

Recommended scales:

| Scale | Finished footprint | Temporary state footprint | Notes |
|---:|---:|---:|---|
| `100%` | `160 mm` | `265 mm` | Best detail. Finished pyramid fits; full temporary state needs splitting. |
| `75%` | `120 mm` | `199 mm` | Best all-around kit scale for Adventurer 4 Pro bed fit. |
| `62.5%` | `100 mm` | `166 mm` | Nice compact display size with readable ramps and courses. |
| `50%` | `80 mm` | `133 mm` | Practical lower limit with a `0.4 mm` nozzle; expect delicate casing/chamber details. |
| `<50%` | `<80 mm` | varies | Treat as a simplified visual model unless details are thickened. |

For small prints, use PLA, `0.12-0.16 mm` layer height, 2-3 walls, and thin-wall handling if available in the slicer. The capstone, chamber reference pieces, and individual ramp segments benefit from a brim.

The modular stackable pieces have `0.35 mm` XY clearance by default around core/fill and fill/ramp-support interfaces. If your printer tends to make tight parts, regenerate with a larger value, for example:

```bash
python3 generate_giza_kit.py --stack-clearance-mm 0.5
```

Slicer scaling also scales the clearances. A `75%` slicer-scale print reduces the default `0.35 mm` clearance to about `0.26 mm`. For the best-fitting modular kit, regenerate at the target physical size and keep `--stack-clearance-mm` at `0.35` or higher.

## Scaling Strategy

For a simple slicer-scale test, start at `75%` or `62.5%`.

For a polished miniature, regenerate with thicker features instead of only scaling down:

```bash
python3 generate_giza_kit.py --base-mm 100 --ramp-width-mm 12 --courses 14 --casing-rings 14
```

Future mini presets should keep casing walls, chamber rods, and the top platform above the nozzle's reliable feature size instead of scaling every detail proportionally.
