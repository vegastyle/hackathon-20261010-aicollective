# Wild Miami — Phase 0 notes (disposable feasibility evidence)

Written 2026-10-10 ~8:30–9:30 AM ET on a headless Linux box (2 vCPU, 3 GB RAM, no Android tooling, no phone).
Nothing here goes in the submission repo unless an organizer approves reuse at 11:15.

## "Confirm first" answers

| # | Status | Finding |
|---|---|---|
| 1 | **CONFIRMED (desktop)** | `litert-lm==0.18.0` (`import litert_lm`) embeds images from the `.litertlm` file: `EmbeddingEngine(path, backend=Backend.CPU(), vision_backend=Backend.CPU())`, `compute_embedding(Content.ImageFile(path), EmbeddingOptions(normalize=True)).embedding` → 768 floats, norm 1.0. → `vectors_generated_by = "litert-lm"`. Load 1.0 s, 1.9 s/image, 895 MB peak RSS on this 2-vCPU box. |
| 2 | OPEN (needs phone) | Docs match the plan: `com.google.mediapipe:tasks-retrieval` (docs say `latest.release` — **pin a version**), `BaseOptions.setModelAssetPath(...)`, `UniversalEmbedderOptions.setTextDelegate/setVisionDelegate(Delegate.GPU)`, `setL2Normalize(true)`, `UniversalEmbedder.createFromOptions(context, opts)`, `embedImage(MPImage)` → `EmbeddingResult.embeddings().get(0)`. Docs only show GPU delegate; CPU unconfirmed. Example app: github.com/google-ai-edge/mediapipe-samples `examples/universal_embedder/android`. |
| 3 | ANSWERED, picked by tuning | Model card: images take **no prefix**. Text: `task: classification \| query: {content}` for classification; `title: none \| text: {content}` for documents; trim whitespace first. (litert-lm JS docs use a different form, `task: search query \| text:` — inconsistent upstream.) Prototype picks the prefix on the tuning split; result is in `out/scoring.json` → `prefix`. Never use float16 (NaN / silent degradation). |
| 4 | **ANSWERED** | `litert-community/embeddinggemma-2-text-vision-440m-litert-lm` and `google/embeddinggemma-2` are both **Apache-2.0**, ungated (no HF license click needed). Quote this in LICENSES.md. |
| 5 | OPEN | Hackathon window: ask organizers. |
| 6 | OPEN | Reuse question: ask at 11:15. |
| 7 | PARTIAL — human must confirm on myfwc.com | myfwc.com returns 403 to automated fetch. Web-search corroboration: Nuisance Alligator Hotline 866-FWC-GATOR (866-392-4286); Wildlife Alert 888-404-FWCC (3922) — for violations; Invasive/Exotic Species Hotline 888-IVE-GOT1 (888-483-4681) — FWC asks for calls on **high-priority** species (nonnative snakes, monitor lizards, tegus); lower-priority (small lizards, iguanas) → IveGot1 app/ivegot1.org. Implication: Burmese python `reportable_sighting → report_nonnative` fits; do not add it for iguana/anoles/toad/treefrog. |

## Model file

- `embeddinggemma-2-text-vision-440m.litertlm`, 387,710,976 bytes (generic CPU/GPU file — **not** the SoC-specific `_Qualcomm_*`/`_Google_Tensor_*` variants in the same repo; if the demo phone's SoC has an NPU variant, that is a *different file and different SHA*, so parity must be rerun).
- SHA-256 `92dcbea108899e5d6e30d919b0744f90d9967e80c67a4ab5503ac16d54f62eb0` (matches HF x-linked-etag).
- URL: https://huggingface.co/litert-community/embeddinggemma-2-text-vision-440m-litert-lm/resolve/main/embeddinggemma-2-text-vision-440m.litertlm
- Model card: image soft tokens 70 or 140 (vision token setting must match on both platforms); Android S26 Ultra GPU text+vision 119 ms, CPU 175 ms / 694 MB.

## Data

- `data/species.csv` — the 30 starting species with `lookalike` = paired species id (great egret → wood stork is one-way).
- `data/photos/<id>__<split>__<obs>.jpg` and `data/negatives/neg__<split>__<obs>.jpg` from iNaturalist (research grade, CC0/CC BY, Florida first, one photo per observation, one observation per observer per species). Attribution per image in `data/credits.csv`.
- Negatives: 30 out-of-catalog Florida animals + 20 plants/fungi/algae as the "non-animal" set (iNat has no scene photos — add a few street/indoor photos by hand if time allows).

- Final set (verified): 330 catalog photos (30 species × 6 p / 2 d / 2 t / 1 r) + 50 negatives (25 d / 25 t); 380 credit rows; no observation in two splits; no hybrids; licenses 268 CC BY, 112 CC0.
- Gotcha fixed: iNat `taxon_name` matches loosely (Green iguana returned *Ctenosaura similis*, which was also a negative; Muscovy and Great egret returned hybrids). `fetch_photos.py` now requires an exact taxon or descendant and rejects hybrids. Result order can shift between runs, so delete files not listed in `credits.csv` after any re-run.

## G0-B: not run (by decision — this machine is for non-model work only)

Run on a machine that can run the model: `python prototype.py --data data --out out` (venv: `litert-lm==0.18.0 numpy pillow requests`). It checks the data, picks prefix + `w` on `d`, tunes θ/δ/possibleFloor under the three limits, evaluates once on `t`, and writes `out/scoring.json` (raw counts + rates, lookalike report, failures, timing), `out/golden.json`, `out/manifest.json` (`vectors_generated_by = litert-lm`). If G0-B fails, change scope and rerun with `--eval-split r`. Expect ~12 min of image embedding at ~2 s/photo on a 2-core CPU. Pack export (`export_pack`/`validate_pack` from the plan) still needs the human-reviewed safety sheet.

## Not done here (needs the phone / team)

- G0-A, G0-C: no phone or Android SDK on this machine.
- G0-B evaluation: see above.
- G0-D: human browser check of myfwc.com pages, record URL + date.
- Safety sheet (origin/conservation/risk/guidance/incident options/blurb) — human-reviewed, not generated.
