# MAISB Android SDK

Production-ready Android SDK for MAISB AI runtime security scanning.

This SDK follows the Claude-provided Android SDK structure and connects to the live MAISB backend:

- `POST /v1/scan` for pre-LLM security scanning
- `POST /v1/sdk/mobile/telemetry` for Phase 4 mobile telemetry
- `GET /health` for backend health checks

## Install inside this repo

Place this folder at:

```text
MAISB/maisb/sdk/android/maisb-android-sdk/
```

Keep the existing Android harness unchanged at:

```text
MAISB/maisb/harness/android/
```

The harness is for benchmark/testing. This folder is the production SDK library.

## Build

```bash
cd MAISB/maisb/sdk/android/maisb-android-sdk
gradle :library:build
gradle :sample:assembleDebug
```

If your machine does not have Gradle installed, open this folder in Android Studio and use **Gradle Sync**, or generate a wrapper:

```bash
gradle wrapper
./gradlew :library:build
```

## Basic app integration

```kotlin
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        MAISB.initialize(
            this,
            MAISBConfig(
                apiKey = "maisb_your_api_key_here",
                tenantId = "default",
                telemetryEnabled = true,
                debug = BuildConfig.DEBUG
            )
        )
    }
}
```

```kotlin
val result = MAISB.getInstance().scan(
    payload = userInput,
    channel = "clipboard",
    objective = "payment_intent"
)

if (result.isBlocked) {
    return
}
```

## Main files

```text
library/src/main/kotlin/com/maisb/shield/MAISB.kt
library/src/main/kotlin/com/maisb/shield/MAISBConfig.kt
library/src/main/kotlin/com/maisb/shield/network/MAISBClient.kt
library/src/main/kotlin/com/maisb/shield/telemetry/TelemetryCollector.kt
library/src/main/kotlin/com/maisb/shield/channels/ChannelDetector.kt
sample/src/main/kotlin/com/maisb/sample/MainActivity.kt
```

## Notes

The sample app uses `maisb_live_test123` only for quick testing. Replace it with a real generated key before demos.
Do not commit production API keys, admin keys, keystores, `.env`, or local build folders.
