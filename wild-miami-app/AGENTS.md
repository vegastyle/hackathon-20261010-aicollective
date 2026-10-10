This is an Expo/React Native mobile application. Prioritize mobile-first patterns, performance, and cross-platform compatibility.

## Expo has changed — do not trust your training data

Expo ships breaking changes every SDK release. APIs you remember are likely renamed, moved, or removed. Before writing any code that touches an Expo, EAS, or React Native API:

1. Read the major version of the `expo` package in `package.json`.
2. Fetch the matching versioned docs: `https://docs.expo.dev/versions/v<major>.0.0/`
3. For anything else, fetch https://docs.expo.dev/llms.txt — an index of all Expo docs with corrections to common LLM misconceptions. Follow its links to the specific page you need; never answer from memory.

## Commands

Use `bunx` instead of `npx` if the project uses bun (`bun.lock` present).

```bash
npx expo install <package>  # ALWAYS use instead of npm/yarn/pnpm/bun add — resolves SDK-compatible versions
npx expo start              # start the dev server
npx expo lint               # lint
npx tsc --noEmit            # typecheck
npx expo-doctor             # diagnose dependency and config issues
npx expo install --fix      # fix incompatible package versions
```

Run lint and typecheck before declaring any task done.

## Wild Miami Android build/test setup

This project has already been smoke-tested on the local Windows Android SDK. In Git Bash, set SDK paths before using adb, emulator, Gradle, or Expo Android commands:

```bash
export ANDROID_HOME=/c/Users/Vega/AppData/Local/Android/Sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
```

Known local tools:

- adb: `C:\Users\Vega\AppData\Local\Android\Sdk\platform-tools\adb.exe`
- emulator: `C:\Users\Vega\AppData\Local\Android\Sdk\emulator\emulator.exe`
- JDK 17: `C:\Program Files (x86)\Android\openjdk\jdk-17.0.14`

For Gradle from Git Bash, also set the Windows-style JDK path:

```bash
export JAVA_HOME='C:\Program Files (x86)\Android\openjdk\jdk-17.0.14'
```

Working AVD:

- `WildMiamiApi36Dev` using `system-images;android-36;google_apis;x86_64`
- The Google Play AVD `WildMiamiApi36` was created too, but it showed `unauthorized` in headless adb testing; prefer `WildMiamiApi36Dev`.

Boot emulator headless:

```bash
emulator -avd WildMiamiApi36Dev -no-window -gpu swiftshader_indirect -no-snapshot-load -no-boot-anim -no-audio
adb shell getprop sys.boot_completed  # wait until this returns 1
```

Build and run debug/dev APK:

```bash
cd wild-miami-app
npx tsc --noEmit
npx expo run:android
```

Or build only:

```bash
cd wild-miami-app/android
cmd.exe //c gradlew.bat assembleDebug
```

The debug APK path is:

```text
wild-miami-app/android/app/build/outputs/apk/debug/app-debug.apk
```

If the app opens to “Unable to load script” in a debug build, start Metro and reverse the port:

```bash
cd wild-miami-app
npx expo start --dev-client --localhost
adb reverse tcp:8081 tcp:8081
adb shell monkey -p com.wildmiami.app 1
```

Orca Android emulator skill commands that worked:

```bash
orca emulator devices --json
orca emulator attach emulator-5554 --json
orca emulator ax --json
orca emulator tap 0.5 0.48 --json
```

Release build caveat: `assembleRelease` failed in the long workspace path with CMake/ninja dirty-manifest/path-length warnings from `expo-modules-core`. Fast mitigation if a release APK is needed: copy `wild-miami-app` to a short path such as `C:\wm`, run `npm install` if needed, then build release there; alternatively reduce native architectures/new-architecture settings before rebuilding.

## Navigation & Routing

- Use **Expo Router** for all navigation. Routes live in `src/app/` — every file there is a screen, `_layout.tsx` files define navigators. Keep non-route code (components, hooks, utils) outside `src/app/`.
- Import `Link`, `router`, and `useLocalSearchParams` from `expo-router`.
- Docs: https://docs.expo.dev/router/introduction.md

## Building with EAS

Use EAS to build, sign, and submit the app in the cloud (`eas build`, `eas submit`) and to ship over-the-air updates (`eas update`) — no local Xcode or Android Studio required. Run EAS CLI as `bunx eas-cli <command>` in Bun projects, or `npx eas-cli@latest <command>` otherwise; substitute that for bare `eas` in docs examples.
Docs: https://docs.expo.dev/eas/index.md

## Rules

- If `ios/` and `android/` directories do not exist, they are generated (Continuous Native Generation). Never create or edit them by hand — configure native behavior in `app.json` and config plugins.
- Expo Go only includes its bundled native modules. After adding a library with native code, the app needs a development build: `npx expo run:ios|android` locally, or `eas build --profile development`.
- Prefer recommended Expo modules over third-party libraries, and check your available skills before adding dependencies. Docs: https://docs.expo.dev/versions/latest/index.md
