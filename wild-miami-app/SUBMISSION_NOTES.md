# Wild Miami release package notes

## APK for manual phone install

Use this APK as the GitHub Release asset:

```text
wild-miami-app/dist/wild-miami-demo-release.apk
```

This is a standalone Android APK built with the JavaScript bundle embedded. It does **not** require Metro, Expo Go, or a USB connection after download.

Build source path used to avoid Windows path-length release failures:

```text
C:\wm
```

Build command:

```bash
cd /c/wm/android
export JAVA_HOME='C:\Program Files (x86)\Android\openjdk\jdk-17.0.14'
export ANDROID_HOME='C:\Users\Vega\AppData\Local\Android\Sdk'
export ANDROID_SDK_ROOT="$ANDROID_HOME"
cmd.exe //c gradlew.bat assembleRelease
```

Output copied from:

```text
C:\wm\android\app\build\outputs\apk\release\app-release.apk
```

To:

```text
wild-miami-app/dist/wild-miami-demo-release.apk
```

Observed APK size: about 73 MB.

## Manual install instructions

1. Upload `wild-miami-demo-release.apk` to the GitHub Release.
2. On the Android phone, download the APK from the release page.
3. Open the downloaded APK.
4. If Android blocks it, enable “Install unknown apps” for the browser or file manager used to open it.
5. Install and open Wild Miami.

If a previous build is already installed and Android refuses to update it, uninstall the old Wild Miami app first, then install the release APK.

## Smoke test result

The release APK was installed on the local Android emulator with:

```bash
adb install -r wild-miami-app/dist/wild-miami-demo-release.apk
adb shell monkey -p com.wildmiami.app 1
```

Orca accessibility tree confirmed the app opens without Metro and shows:

- `Wild Miami`
- `Take photo`
- `Run Demo/FIXTURE identifier`
- `FIXTURE DATA · DEMO IDENTIFIER · NOT FOR SAFETY FACTS`

## Important demo status

This release APK is still a **fixture/demo build**:

- The identifier is deterministic fixture logic, not real Gemma/MediaPipe inference.
- The SQLite database has `user_version = 0`.
- Safety/status/source/photo-credit rows are fixture placeholders.
- The fixture banner is intentionally visible.

## Model status

EmbeddingGemma 2 text-vision 440M LiteRT-LM was downloaded and checksum-verified in Phase 0, and Android packaging is prepared for `.litertlm` assets. The on-device MediaPipe/Gemma embedder is not complete in this APK.

Pinned model SHA-256:

```text
92dcbea108899e5d6e30d919b0744f90d9967e80c67a4ab5503ac16d54f62eb0
```

## Safety choices

- Qualitative labels only: likely / possible / unsure.
- No percentages or probabilities are shown.
- Hotlines appear only inside the incident picker.
- Cards do not say animals are safe to touch.
- Fixture guidance includes: “Watch from a distance. Don’t feed, touch or chase.”
