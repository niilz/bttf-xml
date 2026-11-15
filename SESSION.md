# Session Notes

- Commit formatting is blocked in the container: `./gradlew spotlessApply` cannot download the required JDK 25 from Foojay; no formatter is configured in the Gradle build. A fallback Black installation also fails because the package index is unreachable.
- Merging the Row 2 slots renumbers Row 3 complication/configuration IDs; existing watch configurations may need to be selected again after installation.

- `local.properties` currently points to `sdk.dir=/Users/niilz/Library/Android/sdk` (macOS host path), which does not exist inside the Linux devcontainer (`/workspaces/bttf-xml`). Running `./gradlew` tasks that require the Android SDK inside the container will fail unless an Android SDK is installed/mounted in the container or `ANDROID_HOME` is configured.
- `watchface/src/main/AndroidManifest.xml` defaults to `com.google.wear.watchface.format.version = 1` despite `minSdk = 36` / `compileSdk = 37` (which supports up to WFF v4).
