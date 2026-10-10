# Wild Miami — Implementation Plan (v4.2, handoff)

**Revision 4.2 · Saturday October 10, 2026, 10:00 AM ET** · v4.1 plus everything learned in the first Phase 0 session, written so a fresh machine or session can pick up the remaining Phase 0 work cold.

This file replaces v4.1 as the spec. Code that v4.1 printed inline now lives in the bundle's scripts (listed below); the rules, gates, data contract and safety rules are unchanged except where marked **[v4.2]**.

## What changed in v4.2

- **Confirm #1 answered: yes.** `litert-lm==0.18.0` embeds images from the shipped `.litertlm` file on desktop. Pack vectors are generated with `litert-lm` (`vectors_generated_by = "litert-lm"`, `vector_model_ref` = the model SHA-256). sentence-transformers and torch are dropped from the toolchain.
- **Confirm #3 answered:** images take no prefix; text candidates are `task: classification | query: …`, `title: none | text: …` or none. The prompt prefix is now chosen on the tuning split together with `w` (it is still frozen before the held-out evaluation).
- **Confirm #4 answered:** Apache-2.0, ungated, for both the `.litertlm` repo and `google/embeddinggemma-2`.
- **Model file pinned:** generic `embeddinggemma-2-text-vision-440m.litertlm`, 387,710,976 bytes, SHA-256 `92dcbea108899e5d6e30d919b0744f90d9967e80c67a4ab5503ac16d54f62eb0`. The SoC-specific NPU variants in the same repo are different files; using one means a new SHA-256 and rerunning parity.
- **Data collected and checked:** 330 catalog photos and 50 negatives from iNaturalist with per-image credits. Collection now rejects loose taxon matches and hybrids (see "Data gotchas").
- **FWC numbers corroborated, not yet verified:** all three numbers match across sources. The nonnative hotline is for *high-priority* species only, which changes the incident options for small nonnative animals.
- **New scripts:** `prototype.py` (tune and evaluate on numpy, embedding through `litert-lm`), `pack_tools.py` (schema, build from the reviewed safety sheet, `record-parity`, validator), `fetch_photos.py` (data pull).
- **Incident options must be reviewed:** `pack_tools.py` refuses incident rows without `fwc_source_url` and `reviewed_at`.
- **The first machine can't run models or connect a phone.** It was used only for research, data, scripts and docs. Everything model- or phone-dependent is listed below for the next machine.

## Start here (next machine)

**Time check:** at 10:00 AM ET there are 75 minutes to the 11:15 kickoff. Do the remaining Phase 0 tasks in the priority order below. Anything unfinished at 11:15 is either dropped or done under the Saturday schedule.

### 1. Get the bundle

The bundle (git: `vegastyle/hackathon-prototypes`, folder `wild-miami-phase0/`; or `wild-miami-phase0.tar.gz`) contains: `HANDOFF.md` (this file), `prototype.py`, `pack_tools.py`, `fetch_photos.py`, `data/` (species list, photos, negatives, `credits.csv`, draft `safety_sheet.csv`, draft `incident_options.csv`) and `notes/`. It does **not** include the model or a virtualenv.

```bash
git clone https://github.com/vegastyle/hackathon-prototypes.git && cd hackathon-prototypes/wild-miami-phase0   # or, from the tarball:
# mkdir -p ~/wild-miami-phase0 && tar -xzf wild-miami-phase0.tar.gz -C ~/wild-miami-phase0 && cd ~/wild-miami-phase0
python3.12 -m venv .venv && . .venv/bin/activate && pip install litert-lm==0.18.0 numpy pillow requests
mkdir -p model && curl -L -o model/embeddinggemma-2-text-vision-440m.litertlm \
  https://huggingface.co/litert-community/embeddinggemma-2-text-vision-440m-litert-lm/resolve/main/embeddinggemma-2-text-vision-440m.litertlm
echo "92dcbea108899e5d6e30d919b0744f90d9967e80c67a4ab5503ac16d54f62eb0  model/embeddinggemma-2-text-vision-440m.litertlm" | sha256sum -c
```

Keep this folder **out of the submission repo** until an organizer approves reuse (see "Rules check").

### 2. Remaining Phase 0 tasks, in priority order

| P | Task | Gate | Owner | Needs | Done when |
| --- | --- | --- | --- | --- | --- |
| 1 | Run Google's Universal Embedder example app **unmodified** on the demo phone with the pinned `.litertlm`; record cold load, time per photo, peak memory; time 20 embeddings back to back. **Check whether the CPU delegate works**, since the docs only show GPU | G0-A | ML | Phone, Android Studio | Under 2 s per photo, no crash, numbers in `notes/` |
| 2 | `python prototype.py --data data --out out` (about 12 min of embedding on a 2-core CPU; faster on a laptop) | G0-B | ML + Data | Model-capable machine | `out/scoring.json` meets every G0-B threshold |
| 3 | Scratch Expo dev build with a one-method Kotlin module over USB; model packaging checks; atomic copy with SHA-256 check; clean-install time | G0-C | QA | Phone, JDK 17, Android SDK, Node | Every G0-C check below ticked |
| 4 | Open each FWC page in a **browser**; confirm numbers and incident criteria; fill `source_url` and `verified_at` in `safety_sheet.csv`, and `fwc_source_url` and `reviewed_at` in `incident_options.csv`; resolve the three `VERIFY` conservation statuses | G0-D | Data + safety | A human with a browser | No blank or `VERIFY` cells; every number checked on myfwc.com |
| 5 | Write the 30 blurbs (≤ 200 characters) and pick the display photo and `photo_credit` per species (credits come from `data/credits.csv`) | G0-D | Data + safety | — | `safety_sheet.csv` complete |
| 6 | `python pack_tools.py build --pack-version 1`, then `python pack_tools.py validate` | — | Data | P2 and P4–5 done | "Pack passed validation" (build mode) |
| 7 | Pick the fixed 10-photo parity set (suggest: 2 lookalike pairs × 2 photos + 6 others, from `t`); save their desktop vectors and top-3 lists | G1 prep | ML | P2 done | `out/parity_set.json` saved |
| 8 | Fill local caches: Android SDK, Gradle, npm packages, the model file | — | Everyone | Internet | Builds work with Wi-Fi off |
| 9 | Sketch the six screens; agree the safety copy | — | App | Paper | Done |

If P2 fails G0-B: change scope (drop or swap species, always keeping lookalike pairs together), then run once with `--eval-split r`. Never retune against the same held-out photos.

### 3. Pre-event artifacts are still disposable

Everything in this bundle was made before kickoff. Unless an organizer explicitly approves reuse at 11:15, rerun or rewrite the scripts after kickoff and regenerate every submission asset (`wildlife.db`, vectors, `golden.json`, `scoring.json`). Thresholds and decisions carry over as notes.

## "Confirm first" status

| # | Assumption | Status | Evidence / next step |
| --- | --- | --- | --- |
| 1 | `litert-lm` (Python) can embed images with the `.litertlm` file | **Confirmed** | `EmbeddingEngine(path, backend=Backend.CPU(), vision_backend=Backend.CPU())`; `compute_embedding(Content.ImageFile(path), EmbeddingOptions(normalize=True)).embedding` → 768 floats, norm 1.0. Load 1.0 s, 1.9 s per image, 895 MB peak RSS (2 vCPU). Other options: `vision_tokens_per_image` (card: 70 or 140), `compute_embedding_batch` |
| 2 | Universal Embedder Android API matches the guide | Docs match; **unverified on device** | Dependency `com.google.mediapipe:tasks-retrieval` (docs say `latest.release` — **pin the version you test with** and record it as `android_runtime`). `BaseOptions.builder().setModelAssetPath(...)`, `UniversalEmbedderOptions.builder().setTextDelegate(Delegate.GPU).setVisionDelegate(Delegate.GPU).setL2Normalize(true)`, `UniversalEmbedder.createFromOptions(context, options)`, `embedImage(MPImage)` → `EmbeddingResult.embeddings().get(0)`, `MPImage` from `BitmapImageBuilder(bitmap).build()`. Docs show only the GPU delegate. Example: `github.com/google-ai-edge/mediapipe-samples`, `examples/universal_embedder/android`. Confirm at G0-A |
| 3 | Task prefix / prompt format | **Answered** | No prefix for images. Text: classification `task: classification \| query: {content}`, document `title: none \| text: {content}`; trim whitespace first. Upstream docs disagree (litert-lm's JS sample uses `task: search query \| text:`), so `prototype.py` picks among `none` / `classification` / `document` on the tuning split. The chosen full template lands in `manifest.json` → `prompt_template`. One-photo smoke test (alligator): no prefix ranked crocodile first; both prefixed forms ranked alligator first. Text-only margins between alligator and crocodile were about 0.004, so image prototypes carry the lookalikes |
| 4 | Model license | **Answered: Apache-2.0** | HF metadata for both repos says `apache-2.0`; ungated. Quote the model card in `LICENSES.md` |
| 5 | Hackathon window 11:15 AM–3:45 PM | Open | Ask organizers |
| 6 | Pre-event data, vectors and scripts may not be reused | Open | Ask at 11:15 |
| 7 | Every status, incident option and phone number | **Corroborated, not verified** | myfwc.com returns HTTP 403 to automated fetches; a human must check in a browser. See "FWC findings" |

**Never use float16** with this model: the model card says it returns NaN or silently degraded embeddings.

## FWC findings (to verify at G0-D)

| Action | Number (corroborated) | Use | Page to check |
| --- | --- | --- | --- |
| `call_gator_hotline` | 866-FWC-GATOR (866-392-4286) | Alligator or crocodile believed to pose a threat (FWC: generally at least 4 ft) | myfwc.com/wildlifehabitats/wildlife/alligator/snap/ |
| `report_wildlife_alert` | 888-404-FWCC (888-404-3922) | Wildlife or boating law violations; injured or dead listed species | myfwc.com/contact/incident-reporting/ |
| `report_nonnative` | 888-IVE-GOT1 (888-483-4681) | FWC asks for calls on **high-priority** species: nonnative snakes, monitor lizards, tegus. Lower-priority animals (small nonnative lizards, iguanas) go to the IveGot1 app or ivegot1.org | myfwc.com/wildlifehabitats/nonnatives/report/ |

**[v4.2] Consequence:** keep `reportable_sighting → report_nonnative` for the Burmese python only. Do **not** add it for the green iguana, knight anole, brown anole, cane toad or Cuban treefrog; their card may mention the IveGot1 app as general text, once verified. Also check the incident-reporting page for the injured-manatee number and whether it differs from Wildlife Alert.

## Data delivered (in `data/`)

| File | Contents |
| --- | --- |
| `species.csv` | 30 species: `id, common_name, scientific_name, lookalike` (`lookalike` = paired species id; great egret → wood stork is one-way) |
| `photos/<id>__<split>__<observation>.jpg` | 330 photos: 6 reference `p`, 2 tuning `d`, 2 held-out `t`, 1 reserve `r` per species. iNaturalist research grade, "large" rendition, Florida first, one photo per observation, one observation per observer per species |
| `negatives/neg__<split>__<observation>.jpg` | 50 negatives, 25 `d` + 25 `t`: 30 out-of-catalog Florida animals (bobcat, armadillo, bald eagle, coral snake, black spiny-tailed iguana, pets…) and 20 plants, fungi or algae as the non-animal set |
| `credits.csv` | Per image: file, label, split, observation id, taxon, photographer, license, attribution, source URL. Licenses: 268 CC BY, 112 CC0 |
| `safety_sheet.csv` | **Draft.** Statuses copied from the starting table as working labels; `source_url`, `verified_at`, `blurb`, `photo_credit` blank; three conservation statuses say `VERIFY` (alligator, white ibis, brown pelican). The schema rejects it until a person fills it in |
| `incident_options.csv` | **Draft.** 14 rows from the starting table; `fwc_source_url` and `reviewed_at` blank, and `pack_tools.py` rejects unreviewed rows |

Checked: 380 files ↔ 380 credit rows; no observation ID in two splits; no hybrids; every image opens.

**Data gotchas (fixed in `fetch_photos.py`; keep the fix if you rewrite it after kickoff):**

- iNaturalist's `taxon_name` matches loosely: "Iguana iguana" returned *Ctenosaura similis*, which was also on the negatives list, so one observation sat in two splits. The great egret and Muscovy duck pulls returned hybrids. The fetcher now requires an exact taxon or a descendant and rejects hybrids (`×`).
- Result order shifts between runs; after any re-run, delete image files not listed in `credits.csv`.
- Renamed taxa: use *Nannopterum auritum*, *Pontederia crassipes*, *Trametes sanguinea*.
- iNaturalist can drop connections; the fetcher retries with backoff.
- iNaturalist has no scene photos. If time allows, add a few street, indoor and pet photos by hand as extra non-animal negatives.

## Scripts

| Script | Runs on | What it does |
| --- | --- | --- |
| `prototype.py` | Model machine | Checks data (names, observation separation, references, non-empty splits) → embeds with `litert-lm` (image vectors cached in `out/image_vectors.npz`) → picks prompt prefix and `w` by tuning top-1 (top-3 breaks ties) → tunes θ, δ, `possibleFloor` for correct-likely coverage under wrong-likely ≤ 5%, unknown-likely ≤ 5%, known abstention ≤ 30% (grid adapts to the observed score range) → evaluates once on `--eval-split t` (or `r`) → writes `out/scoring.json` (raw counts and rates, tuning metrics, lookalike report, failures, selection trials, timing), `out/golden.json` (20 stratified known + 5 negatives, tolerance 0.01), `out/manifest.json` |
| `pack_tools.py build --pack-version N` | Model machine | Creates `out/wildlife.db` from the schema, loads the reviewed safety sheet and incident options, embeds the 30 text prototypes with the manifest's `prompt_template`, writes prototypes in deterministic order plus the manifest, sets `user_version`, runs the build-mode validator |
| `pack_tools.py validate [--release]` | Anywhere | Foreign keys, `user_version ≥ 1`, species count, text and image prototype coverage, finite unit-norm vectors, `injured_or_dead` option for every listed species, manifest provenance; `--release` also requires a parity block matching the model SHA-256 and pack version, min cosine ≥ 0.95 and 10/10 identical top-3 |
| `pack_tools.py record-parity …` | Anywhere | Writes the G1 parity block (`--device --android-runtime --backend --min-cosine --top3-identical --photos --checked-at --checked-by`) |
| `fetch_photos.py data` | Anywhere | Re-pulls the photo set (about 8 min) |

Verification done on the first machine without the model: all scripts compile; scoring, tuning, golden selection and the lookalike report behave correctly on synthetic vectors; `pack_tools.py` rejects the draft sheet and passes build mode with filled test data. Release mode fails without parity, passes with good parity and catches bad parity. **Not yet verified:** a real `prototype.py` run and a real `pack_tools.py build`.

Python style for all scripts: explicit module imports only, type hints everywhere, a docstring on every function and module.

## What is already decided — do not reopen

- Stack: EmbeddingGemma 2 text + vision (440M `.litertlm`) → MediaPipe Universal Embedder in a Kotlin Expo module → Expo / React Native, Android only → SQLite via `expo-sqlite`.
- Scope: 30 species (minimum 20 under F1); no 150-species work, no iOS, no live-frame classification.
- Scores are ranking scores, never probabilities; the UI shows only `likely` / `possible` / `unsure`.
- Hotlines appear only through the incident picker.
- **[v4.2]** Pack vectors come from `litert-lm` with the pinned `.litertlm` file.

## Decision and scope

We ship a React Native app that identifies 30 common Miami animals entirely on the phone and gives residents trustworthy local guidance that never encourages touching, feeding or chasing wildlife. A tested 30-species app that works in Airplane Mode is the target.

| In scope | Out of scope (stretch only after G3 passes) |
| --- | --- |
| 30 curated species with lookalike pairs | 150 species, automatic species lists |
| Camera or gallery photo → top 3 with qualitative match labels | Live camera-frame classification |
| Status badge, short blurb, one photo with credit | Image library per species |
| Safety guidance, incident picker and FWC numbers that work offline | In-app "refresh pack" download |
| Offline-capable Android APK installed and verified on a clean phone | iOS, app store publishing |

**Claims we make:** identification of 30 species, entirely offline, with explicit uncertainty. **Claims we don't make:** field-validated accuracy. Our numbers come from 60 known and 25 unknown held-out photos; they are internal hackathon gates, and the README and pitch say so.

## Team and ownership

| Role | Owns | Hands off |
| --- | --- | --- |
| **ML / native** | Kotlin module, atomic model copy, TypeScript scoring, parity check, manifest check | `identify()` working on the phone by G2 |
| **App** | Screens, camera, result and safety cards, incident picker, failure states | UI on the fixture database by 12:15 |
| **Data + safety** | Data pull, pack builder and validator, statuses, incident options, guidance text and numbers | Validated `wildlife.db` by 12:45 |
| **QA + pitch** | Repo, build pipeline, model packaging, signed APK, golden test, licenses, README, demo | Signed, clean-installed APK at G3 |

## Rules check

Under MLH's standard rules, research, data gathering and throwaway experiments are safe before the event; code or files that end up in the submission are not. Building beforehand and open-sourcing it to reuse at the event is not allowed. Teams must credit AI tool use. Confirm against the Hack for Humanity Challenge Guide.

- [ ] **11:15, first thing:** ask an organizer: "Can we reuse a dataset we downloaded beforehand from public APIs, and vectors and scripts we generated from it?" The answer decides Data's 11:15–12:45 plan: rerun or rewrite.
- Do not commit or push this bundle to any GitHub repo before that answer.

## Go/no-go gates

Times assume hacking runs 11:15 AM–3:45 PM. Every ML gate reports raw counts beside rates.

| Gate | When | Owner | Pass | If no-go |
| --- | --- | --- | --- | --- |
| **G0-A** Model on phone | Before kickoff | ML | Google's example app embeds a photo on the demo phone in under 2 s, no crash; cold load and peak memory recorded. ~~Confirm #1~~ done. **[v4.2]** Record which delegate works (GPU / CPU) and the `tasks-retrieval` version | Try a second phone; if none passes, adopt F4 before kickoff |
| **G0-B** Idea works | Before kickoff | Data + ML | Held-out split, settings frozen beforehand: top-3 ≥ 80% (≥ 48/60); wrong-likely ≤ 5% (≤ 3/60); unknown-likely ≤ 5% (≤ 1/25); correct-likely coverage ≥ 40% (≥ 24/60); every lookalike pair separated in the top 3 (`scoring.json` → `lookalikes`) | Revise scope or species, then evaluate once on the reserve split |
| **G0-C** Pipeline works | Before kickoff | QA | Expo dev build with a one-method Kotlin module installs over USB; packaging checks pass; atomic copy with SHA-256 verified; clean-install time recorded | Fix before kickoff |
| **G0-D** Facts verified | Before kickoff | Data + safety | Every status, incident option and number checked on myfwc.com in a browser, with URL and date in the CSVs | Drop the unverified species, option or claim |
| **G1** Engine on phone | Sat 12:30 PM | ML | `embedImage` returns 768 numbers; vectors and top-3 match desktop on the 10-photo parity set (min cosine ≥ 0.95, 10/10 identical); preprocessing and backend recorded; `record-parity` written; `validate --release` passes; warm inference under 2 s | Two people on the module until 1:00; still failing → F4. Ranking mismatch → F2 |
| **G2** End to end | Sat 1:45 PM | ML + QA | Camera → model → SQLite → top 3 → safety card on the validated pack; golden set: species IDs and verdicts match exactly, scores within ±0.01, top-3 ≥ 16/20, top-1 ≥ 12/20; no golden negative returns `likely`; 10 runs, no crash | F1 (with retuning); scope freezes either way |
| **G3** Ship-ready | Sat 3:00 PM | QA | Signed APK built before 2:30; clean install; model checksum verified, loads offline; `validate --release` passes; failure-state tests pass; two Airplane Mode rehearsals; no fixture banner; signing, licenses, credits, numbers, incident options and every card checked | Ship the last passing APK; no new features after 3:00 |

**G0-C model packaging checks**

- [ ] `androidResources { noCompress += "litertlm" }` in `android/app/build.gradle`, surviving `expo prebuild` (config plugin, or re-check after every prebuild).
- [ ] Release build with the model in assets loads it; record APK size (expect ≥ 388 MB of model) and build time.
- [ ] Atomic copy: asset → temp file → size and SHA-256 check (`92dcbea1…62eb0`) → rename into `filesDir`. Kill mid-copy; next launch recovers.
- [ ] Record: model size, storage needed during copy (about 2× model), peak runtime RAM, preprocessing memory, cold load, warm inference.
- [ ] If bundling fails: a working `adb` provisioning script from a clean install; deliverable described as **APK + model**.
- [ ] Total clean-install time recorded (decides whether two G3 rehearsals fit).

**[v4.2] Parity tip:** the desktop vectors in the pack come from litert-lm on **CPU**. If the phone runs the **GPU** delegate, small numeric differences are expected. Parity measures exactly that, so record the backend honestly. If cosine drops below 0.95 on GPU, try the CPU delegate before F2.

## Fallbacks

| ID | Failure | Fallback |
| --- | --- | --- |
| **F1** | Engine works, accuracy short of G2 | Cut to the species that pass on the phone (minimum 20), retune and re-evaluate with the reduced set (cached vectors in `out/image_vectors.npz` make this fast), rebuild with a new `--pack-version` and re-record parity. If out of time, ship the validated pack unchanged or labeled demo mode |
| **F2** | Phone and desktop rankings disagree | Only if the six reference photos per species ship in `assets/reference/`: recompute prototypes on the phone, persist and verify against the golden set (README and parity notes say stored vectors are unused). Otherwise drop F2 and keep the bundled pack |
| **F3** | Too slow or out of memory | Load once, off the UI thread; downscale consistently on both platforms; change `vision_tokens_per_image` (70 or 140) only after rerunning parity and accuracy and updating the manifest; use the strongest verified phone |
| **F4** | No working engine on the phone by 1:00 PM | App ships with the fake identifier labeled "demo mode"; real identification shown on a laptop in Airplane Mode with the same `.litertlm` via `litert-lm`. Say so in the README and pitch |

## Minimal data contract

Three things cross lanes: one SQLite file, one native module and one function.

**Files**

- `assets/wildlife.db` — species, incident options, prototypes and the manifest. Starts as the fixture database (3 species, `user_version = 0`, built at kickoff); replaced with the validated pack (`user_version ≥ 1`) by 12:45. "FIXTURE DATA" banner while `user_version = 0`; G3 fails if it shows.
- `assets/photos/<species_id>.jpg` — one display photo per species (pick from `data/photos`, credit from `credits.csv`).
- Model: `embeddinggemma-2-text-vision-440m.litertlm` in Android assets, uncompressed, copied atomically into `context.filesDir`. Fallback: APK + `adb`-provisioned model in the app's external files directory.
- `assets/reference/` — only if F2 is retained.
- `src/guidance.ts` — reviewed safety text, incident wording and numbers; one owner.
- `src/scoring.ts` — `w`, `θ`, `δ`, `possibleFloor` read from the manifest at startup (fallback copy for tests only).

**SQLite schema:** exactly as in v4.1, now in `pack_tools.py` → `SCHEMA`. Tables `species` (with CHECKs on enums, non-empty `source_url` / `verified_at` / `photo_credit`, blurb ≤ 200, and `risk = 'low' OR default_guidance = 'keep_distance'`), `incident_option` (PK species + incident), `prototype` (768 float32 little-endian, L2-normalized, `length(vec) = 3072`) and `pack_meta` (`manifest` JSON). `PRAGMA foreign_keys = ON` per connection, in the builder and the app. `user_version` 0 = fixture, 1+ = real pack. The app re-checks vector norm on load.

**Manifest** (`pack_meta.manifest`, written by `prototype.py` / `pack_tools.py`, checked by the app)

| Field | Value now | Checked where |
| --- | --- | --- |
| `litertlm_sha256` | `92dcbea108899e5d6e30d919b0744f90d9967e80c67a4ab5503ac16d54f62eb0` | Kotlin module after copy; refuses to load on mismatch |
| `embedding_dim`, `normalization`, `vector_encoding` | 768, L2, float32 little-endian | Builder; app loader |
| `prompt_template` | chosen on tuning split, e.g. `task: classification \| query: a photo of a {common_name} ({scientific_name})` | Builder; F2 recompute |
| `image_preprocessing` | JPEG passed to litert-lm `Content.ImageFile`; litert-lm scales and patchifies; default vision tokens. **Phone:** apply EXIF orientation, pass RGB bitmap; record what MediaPipe does at G1 | Both platforms; frozen at G1 |
| `vectors_generated_by` / `vector_model_ref` | `litert-lm` / the model SHA-256 | Validator |
| `desktop_versions`, `desktop_backend` | litert-lm 0.18.0, numpy; CPU | Recorded |
| `android_runtime`, `backend` | Record at G1 (`tasks-retrieval` version; GPU or CPU) | Recorded via `record-parity` |
| `scoring` | `w`, `theta`, `delta`, `possible_floor` | App loads at startup |
| `parity` | Written at G1 via `record-parity` | `validate --release`, G3 |

**[v4.2] EXIF note:** desktop `litert-lm` takes the file as-is. Before G1, check whether it applies EXIF orientation. If it doesn't, pre-rotate on desktop (PIL `exif_transpose`) and in the Kotlin module, so both platforms see the same pixels. iNaturalist "large" JPEGs are usually already upright, but camera photos often are not.

**Interfaces** (unchanged)

```typescript
// Kotlin Expo module: modules/wild-embedder
export interface WildEmbedder {
  // filesDir first (bundled copy), then external files dir (adb-provisioned); first run copies atomically.
  // Rejects with 'insufficient_storage' | 'checksum_mismatch' | 'model_missing' | 'load_failed'.
  loadModel(expectedSha256: string): Promise<{ loadMs: number; source: 'bundled' | 'provisioned' }>;
  embedImage(photoUri: string): Promise<number[]>;   // 768 floats, L2-normalized; applies EXIF orientation
  embedText(text: string): Promise<number[]>;        // only for F2
}

export type Match = { speciesId: number; score: number }; // raw blended score, NOT a probability
export type Result = { verdict: 'likely' | 'possible' | 'unsure'; matches: Match[] }; // top 3, best first
export declare function identify(photoUri: string): Promise<Result>;
```

**Scoring (identical in Python and TypeScript; reference implementation in `prototype.py`)**

1. Per species: score = w × max cosine over image prototypes + (1 − w) × text-prototype cosine.
2. Rank by raw score; never show it as a probability or percentage.
3. `likely` if top ≥ θ and top − second ≥ δ; else `possible` if top ≥ `possibleFloor`; else `unsure`.
4. Tuning: prompt prefix and `w` by tuning top-1 (top-3 breaks ties); then θ, δ, `possibleFloor` for correct-likely coverage under the three limits (ties: higher unknown rejection, then lower abstention). Freeze; evaluate once on held-out.
5. **[v4.2]** Ties in ranking break by species order (stable sort). Port that exactly to TypeScript.

**Evaluation report:** top-1, top-3, correct-likely coverage, wrong-likely, unknown-likely, unknown rejection, known abstention, each with raw counts (`n_*`) in `scoring.json`. Keep failure examples (`scoring.json` → `failures`) for the pitch and README.

## Phone pipeline (Android)

1. Setup: Android Studio, JDK 17, Node LTS; USB debugging; `adb devices` lists the phone.
2. Dev loop: `npx expo run:android --device`; JS hot-reloads, Kotlin changes need the command again.
3. Model: uncompressed asset → atomic, checksum-verified copy into `context.filesDir`; or tested `adb` script into the external files dir. The Kotlin module resolves both through `Context`; JS never reads the model file.
4. Release: configure signing before `assembleRelease`, install the actual signed output. A debug-signed or EAS preview APK is fine if explicitly identified and tested.
5. Backup: `eas build -p android --profile preview` (needs internet, may queue).
6. Test: clean install, golden set, repeat in Airplane Mode; cold and warm inference; 10 consecutive runs; second device if available.
7. Failure states: insufficient storage, corrupt or wrong-checksum model, corrupt database, interrupted copy, camera permission denied. Each shows its error screen; never a silent fallback to fake identification.

Dry run (scratch, G0-C): blank Expo app → one-method Kotlin module returning a string → model in uncompressed assets, atomically copied and found by the module → the `adb` fallback path → write down every error, fix and timing.

## Saturday schedule

| Lane | Build 11:15–12:30 | Integrate 12:30–1:45 | Harden 1:45–3:00 | Ship 3:00–3:45 |
| --- | --- | --- | --- | --- |
| **ML / native** (critical) | Kotlin module: atomic copy, `embedImage`, 10-photo parity, `record-parity` | TS scoring and verdicts, golden test | Regression only; fallbacks if triggered | Freeze |
| **App** | Screens on fixture database | Real `identify()`, incident picker | Failure states, unsure flow | Freeze |
| **Data + safety** | Fixture DB by 11:30; rerun (if approved) or rewrite `pack_tools.py` / `prototype.py`; validated `wildlife.db` by 12:45 | Final `guidance.ts` and incident options | Final wording and numbers | Freeze |
| **QA + pitch** | Repo (Apache-2.0), debug build, model packaged | Signed candidate APK dry run | Clean-install and Airplane Mode rehearsal ×2 | Submit |
| **Gate** | **G1** 12:30 | **G2** 1:45 | **G3** 3:00 | Submit by 3:30 |

| Time | Checkpoint | Owner |
| --- | --- | --- |
| 11:30 | Organizer answer on reuse; fixture database delivered | Data |
| 12:15 | Camera → fake identifier → fixture DB → safety card | App |
| 12:30 | Kotlin embedding and 10-photo parity pass (**G1**) | ML |
| 12:45 | Real database validated and delivered | Data |
| 1:00 | Real model + real database return top 3 on the phone | ML + App |
| 1:20 | Golden regression and unknown-image smoke test | QA |
| 1:45 | **G2** decision | ML + QA |
| 2:30 | Signed candidate APK | QA |
| 3:00 | **G3** sign-off, release freeze | QA |

**[v4.2] If reuse is not approved:** the after-kickoff rebuild of the data takes about 8 minutes to re-pull (`fetch_photos.py`), about 12 minutes or less to embed, plus the scoring and pack runs. Rewriting the three scripts from this spec is the main cost; the gotchas above are what to keep.

After 3:00: no model, native module, schema or scoring changes except a submission-blocking fix, followed by the full offline smoke test.

## Safety and trust rules (unchanged — these are the product)

1. Never call an animal harmless or safe to touch. Every card ends with "Watch from a distance. Don't feed, touch or chase."
2. `likely`: "Likely match", that species' card, plus two alternatives.
3. `possible`: "Possible match", top 3, the most cautious default guidance among them; species-specific incident options only after the user confirms the animal.
4. `unsure`: "Not sure", top 3 as "Could be one of these", most cautious guidance; never claim an identification; picker offers only verified general instructions.
5. Snakes, alligators and crocodiles always get keep-distance guidance.
6. Never suggest capturing, moving or killing an animal, including nonnative ones.
7. Qualitative labels only; **never a percentage**; say that animals outside the 30-species catalog may not be recognized.
8. Every card shows status source, verification date and photo credit.
9. **Hotlines only through the incident picker**, listing only that species' `incident_option` rows. For an injured animal with no option: general advice to contact a licensed wildlife rehabilitator, no hotline.
10. Each incident option is reviewed against FWC guidance at G0-D; wording says "for example" where the right contact can vary.

## Starting species list

The 30 species, statuses and incident options from v4.1 are now in `data/safety_sheet.csv` and `data/incident_options.csv` (drafts to verify at G0-D). Lookalike pairs: green iguana ↔ knight anole, brown ↔ green anole, alligator ↔ crocodile, raccoon ↔ opossum, white ibis ↔ wood stork, great egret → wood stork. **[v4.2]** No nonnative-hotline rows for the iguana, anoles, cane toad or Cuban treefrog (see "FWC findings").

## Licensing and attribution

| Item | Record |
| --- | --- |
| Application code | Apache-2.0 (repo license) |
| Model and weights | **[v4.2]** Apache-2.0 per the `litert-community/embeddinggemma-2-text-vision-440m-litert-lm` and `google/embeddinggemma-2` model cards; quote them in `LICENSES.md` |
| Photographs | Per image from `credits.csv`: photographer, license (CC BY or CC0 only), source URL. CC BY requires visible attribution on the card |
| Species text and status data | Our wording; FWC pages cited per species via `source_url` |
| AI tools | List which tools were used and for what (this plan and scripts were drafted with Claude Code) |

## Other risks

| Risk | Mitigation |
| --- | --- |
| Organizers rule pre-event data, vectors or scripts out | Ask at 11:15; plan the rewrite either way |
| Small evaluation sample | Raw counts; no field-accuracy claims; show failures honestly |
| Venue Wi-Fi fails | Caches: SDK, Gradle, npm, model file (388 MB) |
| Phone, cable or battery fails | Two cables, power bank, fully provisioned second phone |
| Large APK slows installs | Clean-install time measured at G0-C; `adb` provisioning for rehearsals if needed |
| float16 errors | Never float16; `litert-lm` path uses the quantized model as shipped |
| GPU vs CPU numeric drift | Parity measures it; try the CPU delegate before F2 |
| EXIF orientation mismatch | Check at G1; pre-rotate on both platforms if needed |
| iNaturalist name drift and loose matching | Exact taxon filter, hybrid rejection, orphan cleanup |

## Acceptance tests and release policy (unchanged)

Provisioning on a clean phone, checksum matches, Airplane Mode before the first identification · configuration lock across platforms (any change reruns parity, evaluation and golden) · vector provenance matches how vectors were made · parity block present and matching (`validate --release`) · retrieval parity on the 10-photo set · evaluation with separate observations across splits and all seven metrics with raw counts, held-out evaluated once per configuration · pack integrity · failure states tested · every hotline, status and incident option verified, no hotline outside the picker · last known-good signed artifact retained at G3 · everything in the submission created after kickoff unless reuse is approved.

## Sources

- [EmbeddingGemma 2 model card](https://huggingface.co/google/embeddinggemma-2)
- [LiteRT Community: EmbeddingGemma 2 text-vision 440M](https://huggingface.co/litert-community/embeddinggemma-2-text-vision-440m-litert-lm)
- [LiteRT-LM embedding models](https://developers.google.com/edge/litert-lm/embedding_models)
- [Universal Embedder for Android](https://developers.google.com/edge/mediapipe/solutions/retrieval/universal_embedder/android)
- [MediaPipe Universal Embedder guide](https://developers.google.com/edge/mediapipe/solutions/retrieval/universal_embedder)
- [iNaturalist API docs](https://api.inaturalist.org/v1/docs/)
- [FWC: report nonnative species](https://myfwc.com/wildlifehabitats/nonnatives/report/)
- [FWC: Statewide Nuisance Alligator Program](https://myfwc.com/wildlifehabitats/wildlife/alligator/snap/)
- [FWC: living with alligators and crocodiles](https://myfwc.com/conservation/you-conserve/wildlife/alligators/)
- [FWC: incident reporting](https://myfwc.com/contact/incident-reporting/)
- [MLH standard hackathon rules](https://github.com/MLH/mlh-policies/blob/main/standard-hackathon-rules.md)
