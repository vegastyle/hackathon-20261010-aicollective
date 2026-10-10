# Wild Miami app skeleton notes — 2026-10-10

## Current state

- Created local Expo / React Native TypeScript app in `wild-miami-app/`.
- Installed `expo-sqlite` and `expo-image-picker`.
- Added runtime SQLite fixture database with `PRAGMA user_version = 0`.
- Added clear `FIXTURE DATA · DEMO IDENTIFIER` banner.
- Added screens/flows:
  - home/camera
  - camera input
  - gallery input
  - demo fixture identifier
  - result with qualitative labels only (`likely`, `possible`, `unsure`)
  - top-3 alternatives
  - species safety card
  - incident picker
  - error/failure state
- Added TypeScript scoring shape:
  - `Match = { speciesId: number; score: number }`
  - `Result = { verdict: 'likely' | 'possible' | 'unsure'; matches: Match[] }`
  - stable species-order tie-breaking

## What is real vs fixture

Real:
- Expo app workspace and TypeScript UI flow.
- SQLite integration path.
- Scoring/result TypeScript contract.
- Stable tie-breaking implementation.

Fixture/demo:
- Species rows, safety text, status/source/verification/photo credit.
- Incident guidance and phone rows.
- Identifier uses a deterministic fixture hash of the photo URI; it is not ML.
- Runtime DB is created on device rather than loaded from final `assets/wildlife.db`.
- Native model module is represented by `src/nativeWildEmbedder.ts`, but no Kotlin implementation exists yet.

## Gate status

- G0-A: not run; `adb` is not on PATH in this shell.
- G0-B: previous Phase 0 run is NO-GO. Do not retune on held-out split `t`.
- G0-C: not run; Android SDK/adb/device needed.
- G0-D: not done; human browser verification required before filling facts.

## Next actions

1. Run the app locally with Expo, preferably on Android.
2. Install/configure Android SDK + adb, then attach an emulator/device with Orca Android emulator tooling.
3. Replace runtime fixture DB with a generated `assets/wildlife.db` once organizer approval/data path is clear.
4. Add Kotlin Expo module skeleton for `loadModel(expectedSha256)` and `embedImage(photoUri)`.
5. Keep fixture banner until `user_version >= 1` and all reviewed safety data is present.

Do not push or submit this with pre-event Phase 0 assets unless organizer approval and repo target are explicit.
