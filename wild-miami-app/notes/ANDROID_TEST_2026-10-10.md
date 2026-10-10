# Android test notes — 2026-10-10

## Tooling discovered

- Android SDK: `C:\Users\Vega\AppData\Local\Android\Sdk`
- adb: `C:\Users\Vega\AppData\Local\Android\Sdk\platform-tools\adb.exe`
- emulator: `C:\Users\Vega\AppData\Local\Android\Sdk\emulator\emulator.exe`
- JDK 17: `C:\Program Files (x86)\Android\openjdk\jdk-17.0.14`

Useful Git Bash env:

```bash
export ANDROID_HOME=/c/Users/Vega/AppData/Local/Android/Sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
```

For Windows Gradle commands, set:

```bash
export JAVA_HOME='C:\Program Files (x86)\Android\openjdk\jdk-17.0.14'
```

## Emulator

Created AVDs:

- `WildMiamiApi36` using `system-images;android-36;google_apis_playstore;x86_64`
  - Problem: showed `unauthorized` in adb when run headless; not useful for automated testing.
- `WildMiamiApi36Dev` using `system-images;android-36;google_apis;x86_64`
  - Works with adb.
  - Booted headless with:

```bash
emulator -avd WildMiamiApi36Dev -no-window -gpu swiftshader_indirect -no-snapshot-load -no-boot-anim -no-audio
```

Boot check passed: `adb shell getprop sys.boot_completed` returned `1`.

## Build/test

- `npx tsc --noEmit`: PASS
- `npx expo config --type public`: PASS
- `./gradlew assembleDebug`: PASS
  - Debug APK: `wild-miami-app/android/app/build/outputs/apk/debug/app-debug.apk`
  - Size observed: about 138 MB
- Installed debug APK on `emulator-5554`: PASS
- `npx expo run:android`: PASS and bundled JS through Metro.
- Orca emulator attach: PASS
- UI smoke via Orca accessibility tree: PASS
  - Home screen shows `Wild Miami`, fixture banner, Take photo, Choose from gallery, Demo/FIXTURE button.
  - Demo/FIXTURE button opens result screen.
  - Result screen shows qualitative verdict, top-3 alternatives, and species safety card.

## Known issue

`assembleRelease` failed in this long workspace path with CMake/ninja dirty-manifest/path-length warnings from `expo-modules-core`. Debug/dev build is working. Fast mitigation if release is needed: move/copy `wild-miami-app` to a much shorter path (for example `C:\wm`) and run release build there, or reduce native architectures/new-architecture settings before rebuilding.

## Still fixture

This verifies the app skeleton and fixture/demo flow only. It does not verify real ML, real safety facts, or the final SQLite pack.
