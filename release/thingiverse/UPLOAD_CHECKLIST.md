# Maker-Site Upload Checklist

Use this for Thingiverse, Printables, MakerWorld, or a similar model host.

## Build The Upload Packet

```bash
make release
```

This regenerates the STL files, validates geometry, creates preview images, copies the curated release files into `release/thingiverse/upload_bundle/`, and creates:

```text
release/thingiverse/giza-pyramid-construction-theory-stl-kit-v0.1.0.zip
```

## Upload Files

Recommended upload:

- Main file: `giza-pyramid-construction-theory-stl-kit-v0.1.0.zip`
- Optional individual files for browsing:
  - `constructed_01_full_backfilled_ramp_system.stl`
  - `constructed_02_capstone_set_before_deramping.stl`
  - `constructed_03_partial_top_down_deramping.stl`
  - `constructed_04_finished_pyramid.stl`

## Images

Use these generated renders in this order:

1. `images/cover_full_ramp_system.png`
2. `images/capstone_before_deramping.png`
3. `images/partial_top_down_deramping.png`
4. `images/finished_pyramid.png`

Replace them with real print photos once available.

## Listing Fields

- Title: `Giza Pyramid Construction Theory STL Kit`
- Summary: use the `Short Summary` section from `LISTING.md`
- Description: use `LISTING.md`
- Category: Education, Architecture, Models, or Historical depending on the site taxonomy
- Tags: copy the tag list from `LISTING.md`
- License: confirm before publish

## License Decision

Recommended: Creative Commons Attribution-NonCommercial-ShareAlike 4.0.

This is only a recommendation. Pick the final license deliberately in the platform UI before publishing. If you want commercial print sales allowed, use a less restrictive Creative Commons license instead.

## Final QA

- Run `make validate`
- Open the four constructed state STLs in a slicer
- Confirm the capstone area has no collar/shelf artifact
- Confirm the full temporary state fits only at the intended scale
- Confirm the description says this is conceptual, not archaeological proof
- Confirm the GitHub link is live
- Confirm the selected license matches your intent
