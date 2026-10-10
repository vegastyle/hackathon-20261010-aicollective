# Wild Miami app skeleton

Android-first Expo/React Native prototype for the hackathon submission.

## Run

```bash
cd wild-miami-app
npm install
npm run android
```

If no Android SDK/device is configured, run `npx expo start` and open it from Expo Go.

## Current deliverable

- Expo + TypeScript app.
- SQLite via `expo-sqlite`.
- Runtime fixture database with `PRAGMA user_version = 0`.
- Visible `FIXTURE DATA · DEMO IDENTIFIER` banner.
- Camera and gallery input plus explicit Demo/FIXTURE path.
- Result flow with `likely` / `possible` / `unsure`, top-3 alternatives, species safety card, incident picker, and error state.
- TypeScript scoring contract with stable species-order tie-breaking.
- Android native project generated with `expo prebuild --platform android`.
- `.litertlm` model assets configured as uncompressed in `android/app/build.gradle`.

## Fixture warning

This build does **not** contain verified safety facts or real ML. Do not remove the fixture banner until a validated `assets/wildlife.db` with `user_version >= 1` replaces the fixture database and all safety data is human-reviewed.

Hotlines are only displayed inside the incident picker. Current phone rows are fixture placeholders and must be verified before release.

## Android/emulator status

The Orca Android emulator skill was installed, but this shell currently has no `adb` on PATH and `orca emulator devices --json` returned no devices. Android testing is blocked until Android SDK/emulator or a USB-debugging phone is available.

## Native model path

`src/nativeWildEmbedder.ts` records the pinned model SHA-256 and the Kotlin Expo module interface. It deliberately throws until the native module exists, so the app cannot silently claim fixture mode is real ML.

`android/app/src/main/assets/MODEL_ASSET_README.md` marks where the `.litertlm` file can go if bundling is approved. The real model file is intentionally not committed.
