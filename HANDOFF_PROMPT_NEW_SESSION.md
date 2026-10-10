# Handoff prompt for new Wild Miami session

```text
You are taking over Wild Miami, a hackathon Android/Expo project. Time is critical: it is noon and we need to move from Phase 0 into building the app.

Repo/workspace:
- Current repo: https://github.com/vegastyle/hackathon-prototypes.git private
- Working folder of the Phase 0 bundle: wild-miami-phase0/
- First file to read fully: wild-miami-phase0/HANDOFF.md
- Also read: wild-miami-phase0/notes/SESSION_REPORT_2026-10-10.md

Important rules:
- Do NOT push, create a public repo, or submit pre-event scripts/assets unless I explicitly confirm organizer approval for reuse.
- Do NOT invent or fill safety facts, statuses, FWC phone numbers, verification dates, or source URLs. G0-D requires a human checking myfwc.com in a browser.
- Hotlines only through incident picker.
- Do not claim probabilities; scores are only ranking scores. UI labels: likely / possible / unsure.
- Never say animals are safe to touch. Every safety card must end with: “Watch from a distance. Don’t feed, touch or chase.”
- If doing ML after the failed held-out result, do not retune on held-out split t. Scope change first, then evaluate once on reserve split r.

What was done in the previous session:
- Cloned/checked out `vegastyle/hackathon-prototypes`, folder `wild-miami-phase0`.
- Read `HANDOFF.md` fully.
- Created Python 3.12 venv with uv at `wild-miami-phase0/.venv`.
- Installed:
  - `litert-lm==0.18.0`
  - `numpy==2.5.3`
  - `pillow==12.3.0`
  - `requests==2.34.2`
- Downloaded model:
  - `wild-miami-phase0/model/embeddinggemma-2-text-vision-440m.litertlm`
- Verified SHA-256 OK:
  - `92dcbea108899e5d6e30d919b0744f90d9967e80c67a4ab5503ac16d54f62eb0`
- Ran:
  - `wild-miami-phase0/.venv/Scripts/python.exe prototype.py --data data --out out`
- Artifacts created:
  - `wild-miami-phase0/out/scoring.json`
  - `wild-miami-phase0/out/golden.json`
  - `wild-miami-phase0/out/manifest.json`
  - `wild-miami-phase0/out/image_vectors.npz`
  - `wild-miami-phase0/notes/g0b_env_model_check.log`
  - `wild-miami-phase0/notes/g0b_prototype_t_20261010_112554.log`
  - `wild-miami-phase0/notes/SESSION_REPORT_2026-10-10.md`

G0-B result from held-out split t:
- Decision: NO-GO
- top-3: 57/60 = 95.0% PASS, threshold ≥ 48/60
- wrong-likely: 1/60 = 1.67% PASS, threshold ≤ 3/60
- unknown-likely: 2/25 = 8.0% FAIL, threshold ≤ 1/25
- correct-likely coverage: 25/60 = 41.67% PASS, threshold ≥ 24/60
- lookalikes: FAIL; not all lookalike held-out examples had true species in top 3
  - Green iguana vs Knight anole: one Green iguana held-out image not in top 3
  - American alligator vs American crocodile: one American alligator held-out image not in top 3

G0-A/G0-C were skipped:
- `adb` was not installed / not on PATH.
- No connected Android phone was visible.
- Node exists (`v22.18.0`), but Android tooling was not available.

G0-D remains human/manual:
- Do not fill these automatically.
- `data/safety_sheet.csv` blanks:
  - `source_url`: blank for all 30 species
  - `verified_at`: blank for all 30 species
  - `blurb`: blank for all 30 species
  - `photo_credit`: blank for all 30 species
  - `conservation_status`: VERIFY on CSV lines 6, 18, 21
- `data/incident_options.csv` blanks:
  - `fwc_source_url`: blank for all 14 rows
  - `reviewed_at`: blank for all 14 rows

Your mission now:
We are past Phase 0 and need to start building. Prioritize a working app skeleton and integration path over perfect ML.

Start by:
1. Read `wild-miami-phase0/HANDOFF.md` and `wild-miami-phase0/notes/SESSION_REPORT_2026-10-10.md`.
2. Check whether the organizer approved reuse of pre-event data/scripts/vectors. If I have not explicitly said yes, keep pre-event assets out of any submission repo and treat them as reference only.
3. Create or identify the actual app workspace/repo for the hackathon submission. If none exists, ask me whether to create one locally.
4. Build the app skeleton:
   - Expo / React Native Android-only
   - SQLite via `expo-sqlite`
   - camera/gallery input placeholder if camera setup is too slow
   - screens:
     - home/camera
     - result with likely/possible/unsure
     - top-3 alternatives
     - species safety card
     - incident picker
     - error/failure state
   - fixture database first with `user_version = 0` and clear “FIXTURE DATA” banner
5. Implement TypeScript scoring shape now, even if the embedder is mocked:
   - types:
     - `Match = { speciesId: number; score: number }`
     - `Result = { verdict: 'likely' | 'possible' | 'unsure'; matches: Match[] }`
   - stable species-order tie-breaking
   - qualitative labels only, no percentages
6. Add a fake/mock identifier behind an obvious `DEMO/FIXTURE` path so UI can progress while native model work catches up.
7. If Android SDK and phone are available, start G0-C/G1 native path:
   - one-method Kotlin Expo module
   - `loadModel(expectedSha256)`
   - atomic copy placeholder / real implementation if possible
   - checksum verification for the pinned model
   - `embedImage(photoUri)` stub first, then real MediaPipe Universal Embedder if time allows
8. For data:
   - Do not fill FWC facts yourself.
   - If organizer approved reuse, use existing Phase 0 outputs as inputs.
   - If not approved, use fixture data for app development and plan to regenerate/rewrite after kickoff.

Immediate deliverable:
- A runnable Expo Android app skeleton with fixture DB/data and fake identifier.
- README or notes file explaining current gate status, what is real vs fixture, and next actions.
- Do not push unless I explicitly tell you organizer approval + repo target.

Be concise, move fast, and record decisions in `notes/`.
```
