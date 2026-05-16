# Run from repo root or SDK folder after uploading the SDK.
cd .\maisb\sdk\android\maisb-android-sdk

gradle :library:build
gradle :sample:assembleDebug

# If you generated the Gradle wrapper, use:
# .\gradlew.bat :library:build
# .\gradlew.bat :sample:assembleDebug
