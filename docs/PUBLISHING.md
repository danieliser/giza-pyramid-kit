# Publishing Checklist

This project is intended to publish as a standalone GitHub repository from the `giza-pyramid-kit/` directory.

## Before First Push

1. Choose a license.
   - No open-source license has been selected yet.
   - Until a license is added, public GitHub visitors can view the code but do not receive reuse rights.
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
