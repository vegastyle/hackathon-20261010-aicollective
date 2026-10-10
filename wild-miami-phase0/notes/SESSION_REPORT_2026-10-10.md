# Wild Miami Phase 0 session report — 2026-10-10

## Scope / rules followed

- Read `HANDOFF.md` fully before running Phase 0 work.
- Did not fill in FWC safety facts, phone numbers, statuses, source URLs, or verification dates.
- Did not push, create a public repo, or submit pre-event assets to a remote repo.
- Evaluated G0-B once on held-out split `t`; because it failed one threshold, did **not** retune against held-out photos.

## Environment setup completed

Working directory: `wild-miami-phase0/`

- Created Python 3.12 virtualenv at `.venv/` using `uv`.
- Installed required packages:
  - `litert-lm==0.18.0`
  - `numpy==2.5.3`
  - `pillow==12.3.0`
  - `requests==2.34.2`
- Downloaded pinned model to `model/embeddinggemma-2-text-vision-440m.litertlm`.
- Verified model SHA-256:
  - expected: `92dcbea108899e5d6e30d919b0744f90d9967e80c67a4ab5503ac16d54f62eb0`
  - result: `OK`
- Environment/model proof saved in `notes/g0b_env_model_check.log`.

## G0-B run completed

Command run:

```bash
.venv/Scripts/python.exe prototype.py --data data --out out
```

Artifacts written locally:

- `out/scoring.json`
- `out/golden.json`
- `out/manifest.json`
- `out/image_vectors.npz` — cached image vectors for faster subsequent runs
- raw log: `notes/g0b_prototype_t_20261010_112554.log`

Frozen settings selected on tuning split:

- prompt prefix: `document`
- `w`: `0.75`
- `theta`: `0.866`
- `delta`: `0.01`
- `possible_floor`: `0.8605`
- eval split: `t`

Timing:

- `images_embedded`: `350`
- `mean_image_seconds`: `3.4454006319999877`

## G0-B held-out result against thresholds

| Metric | Result | Threshold | Gate |
| --- | ---: | ---: | --- |
| top-3 | 57/60 = 95.0% | >= 48/60 = 80.0% | PASS |
| wrong-likely | 1/60 = 1.67% | <= 3/60 = 5.0% | PASS |
| unknown-likely | 2/25 = 8.0% | <= 1/25 = 4.0% | **FAIL** |
| correct-likely coverage | 25/60 = 41.67% | >= 24/60 = 40.0% | PASS |
| lookalike true in top 3 | not all separated | every lookalike pair separated in top 3 | **FAIL** |

Additional held-out metrics:

- top-1: 48/60 = 80.0%
- known abstention: 23/60 = 38.33%
- unknown rejection: 20/25 = 80.0%

G0-B decision: **NO-GO** under the v4.2 thresholds.

Failure reasons:

1. Unknown-likely exceeded threshold: 2/25 instead of <= 1/25.
2. Lookalike report includes held-out examples where `true_in_top3` is false:
   - Green iguana vs Knight anole: one Green iguana held-out image not in top 3.
   - American alligator vs American crocodile: one American alligator held-out image not in top 3.

Per spec, next ML action is **scope change first**, keeping lookalike pairs together, then evaluate once with `--eval-split r`. Do not retune on held-out `t`.

## G0-A / G0-C status

Skipped in this session.

Reason:

- No Android phone connection was available to this shell.
- `adb` was not installed / not on PATH (`adb: command not found`).
- Node was present (`v22.18.0`), but Android tooling required for USB/device work was unavailable.

## G0-D status / blanks left for human review

No G0-D facts were filled. A human must check `myfwc.com` in a browser before these can be completed.

Remaining blanks / `VERIFY` cells:

### `data/safety_sheet.csv`

- `source_url`: blank for all 30 species.
- `verified_at`: blank for all 30 species.
- `blurb`: blank for all 30 species.
- `photo_credit`: blank for all 30 species.
- `conservation_status`: `VERIFY` on 3 rows:
  - CSV line 6
  - CSV line 18
  - CSV line 21

### `data/incident_options.csv`

- `fwc_source_url`: blank for all 14 rows.
- `reviewed_at`: blank for all 14 rows.

## Local changes / artifacts created

Tracked/untracked notes created:

- `notes/g0b_env_model_check.log`
- `notes/g0b_prototype_t_20261010_112554.log`
- `notes/SESSION_REPORT_2026-10-10.md`

Ignored local artifacts created:

- `.venv/`
- `model/embeddinggemma-2-text-vision-440m.litertlm`
- `out/`

These ignored artifacts are intentionally not suitable for pushing unless the organizer approves reuse and the team decides how to handle generated assets.

## Next actions by gate

- **G0-A:** NO-GO / not run. Install Android tooling, connect phone, run Google's Universal Embedder example unmodified with pinned model; record cold load, per-photo time, peak memory, delegate, and tasks-retrieval version.
- **G0-B:** NO-GO. Change scope, keeping lookalike pairs together; then run exactly once with `--eval-split r` and record raw counts/rates.
- **G0-C:** NO-GO / not run. With phone + JDK 17 + Android SDK + Node, create scratch Expo dev build with one-method Kotlin module, packaging checks, atomic copy + SHA-256, and clean-install timing.
- **G0-D:** NO-GO / human needed. Verify FWC pages in browser, fill source/review columns, resolve `VERIFY` statuses, write blurbs, and choose photo credits from `data/credits.csv`.
