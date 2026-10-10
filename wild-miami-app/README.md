# Wild Miami app skeleton

Android-first Expo/React Native prototype for the hackathon submission.

## Run during development

```bash
cd wild-miami-app
npm install
npm run android
```

If no Android SDK/device is configured, run `npx expo start` and open it from Expo Go.

## Manual install release APK

For phone installation from a GitHub Release, upload this standalone APK as the release asset:

```text
wild-miami-app/dist/wild-miami-demo-release.apk
```

On the phone:

1. Download the APK from the GitHub Release.
2. Open the downloaded APK.
3. If Android blocks it, allow “Install unknown apps” for the browser/file manager.
4. Install and open Wild Miami.

This release APK has the JS bundle embedded and does not require Metro or Expo Go.

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

The local Android SDK was found at `C:\Users\Vega\AppData\Local\Android\Sdk`. A working emulator AVD, `WildMiamiApi36Dev`, was created and used for smoke testing.

Release APK status:

- Built from short path `C:\wm` to avoid Windows path-length issues.
- Copied to `wild-miami-app/dist/wild-miami-demo-release.apk`.
- Installed successfully on the local Android emulator.
- Opened without Metro and showed the Wild Miami fixture/demo home screen.

## Native model path

`src/nativeWildEmbedder.ts` records the pinned model SHA-256 and the Kotlin Expo module interface. It deliberately throws until the native module exists, so the app cannot silently claim fixture mode is real ML.

`android/app/src/main/assets/MODEL_ASSET_README.md` marks where the `.litertlm` file can go if bundling is approved. The real model file is intentionally not committed.
