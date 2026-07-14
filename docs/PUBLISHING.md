# Publishing Checklist

This project is intended to publish as a standalone GitHub repository from the `giza-pyramid-kit/` directory.

## Before First Push

1. Confirm the dual-license notices are included.
   - Software source: MIT (`LICENSE`).
   - Models, generated STLs, images, and documentation: CC BY-NC-SA 4.0 (`LICENSE-ASSETS.md`).
2. Regenerate the STL kit:

   ```bash
   make generate
   ```

3. Validate geometry:

   ```bash
   make validate
   ```

4. Smoke-test the browser demo:

   ```bash
   make serve
   ```

   Open `http://localhost:8026/demo/`.

5. Review generated file size:

   ```bash
   du -sh .
   ```

   The current repository is small enough for ordinary GitHub hosting.

## Suggested First Commit

```bash
git add .
git commit -m "Initial Giza pyramid STL kit"
```

## Suggested GitHub Setup

Using GitHub CLI:

```bash
gh repo create giza-pyramid-kit --public --source=. --remote=origin --push
```

Or create an empty GitHub repository in the browser, then:

```bash
git remote add origin git@github.com:YOUR_USER/giza-pyramid-kit.git
git push -u origin main
```

## GitHub Pages Demo

The browser demo is static. Once pushed, GitHub Pages can serve the repository root or a Pages branch, and the demo can be opened at `/demo/` after the generated `dist/` files are present.

Because `dist/` contains the downloadable STL kit, it is intentionally kept in version control. `.gitattributes` marks STL files as binary/generated to avoid noisy diffs.

This repo is configured to publish from `main` at the repository root with `.nojekyll` enabled. The expected live URL is [the animated demo](https://danieliser.github.io/giza-pyramid-kit/demo/).

## Maker-Site Release

Use this for Thingiverse, Printables, MakerWorld, or similar STL hosts:

```bash
make release
```

The release target regenerates and validates the STL set, creates simple PNG renders, builds a curated upload folder, and writes:

```text
release/thingiverse/giza-pyramid-construction-theory-stl-kit-v0.1.0.zip
```

The maker-site copy lives in:

```text
release/thingiverse/LISTING.md
release/thingiverse/UPLOAD_CHECKLIST.md
release/thingiverse/LICENSE_NOTE.md
```

Select `Creative Commons Attribution-NonCommercial-ShareAlike 4.0` in the maker platform's upload UI so the listing matches `LICENSE-ASSETS.md` in the bundle.

Replace the generated preview renders with real print photos when a physical test print is available.
