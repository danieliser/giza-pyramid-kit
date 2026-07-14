# Author Toolkit Voice Analysis

Analyzed: `docs/BLOG_POST_DRAFT.md`

Date: 2026-07-14

## Fidelity Gate

- Tool: `scripts/voice-verify.py`
- Model: `AnnaWegmann/Style-Embedding`
- Mode: discriminative margin
- Author references: 4 posts from `danieliser.com`
- Contrasting references: 14 Popup Maker documents and posts
- Draft score: `-0.0447`
- Author reference median: `0.0762`
- Robust z-score: `-1.33`
- Result: `WARN`

The pass threshold is `z >= -1.0`. The draft is slightly off-center for the
personal-site corpus, but it is much closer to passing than failing. The fail
threshold is `z < -3.0`.

## Structural Fingerprint Lint

### Matches

- Paragraphs are compact: 2.21 sentences on average.
- The article is direct, specific, and grounded in the actual build process.
- It avoids the profile's corporate and robotic vocabulary.
- Caveats are explicit without becoming apologetic.
- The opening uses questions, contrast, and first-person motivation effectively.

### Drift

- Short sentences are underrepresented: 13.2% versus the profile's 25% target.
- First-person texture is light for a personal blog post: 9 uses of `I` across
  roughly 1,500 prose words.
- Most section openers are descriptive (`The model...`, `The repo...`, `The
  capstone...`) rather than problem, experience, or contrarian openers.
- The draft does not use the profile's characteristic transitions. This is not
  a reason to force catchphrases, but it does explain part of the embedding gap.
- Several sentences exceed 30 words and carry multiple ideas. The most visible
  examples are the project-summary sentence in the introduction and the
  watertight-mesh explanation in the geometry review.

## Recommended Revision Pass

1. Rework 3 to 5 section openers around a concrete problem or discovery from
   building the model.
2. Split the longest explanatory sentences and add a few short conclusions.
3. Add 2 or 3 specific first-person moments from the modeling process.
4. Preserve the current caveats, technical specificity, and restrained tone.
5. Re-run the same fidelity gate after revision; do not optimize solely for the
   score if the prose becomes less natural.

## Reproduction

```bash
cd ~/Toolkit/author-toolkit
python3 -m venv .venv
.venv/bin/pip install sentence-transformers
.venv/bin/python scripts/voice-verify.py \
  --draft ~/Projects/Gambles/giza-pyramid-kit/docs/BLOG_POST_DRAFT.md \
  --references ~/Projects/ProContent/author-writing-samples/danieliser.com \
  --impostors ~/Projects/ProContent/author-writing-samples/wppopupmaker-content/docs,~/Projects/ProContent/author-writing-samples/wppopupmaker-content/page,~/Projects/ProContent/author-writing-samples/wppopupmaker-content/post,~/Projects/ProContent/author-writing-samples/wppopupmaker-content/tutorial \
  --json
```
