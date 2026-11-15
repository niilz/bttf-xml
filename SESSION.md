# Session Notes

- The `remove long-value` commit disables LONG_TEXT in supportedTypes but leaves its rendering branches in XML. These unused branches still expand the XML and could be removed separately.

- Per-character segment rendering uses fixed cells. Bundled `.`, `,`, and `:` glyphs have zero advance from the earlier font customization; their optical placement in mixed numeric strings still needs on-device verification (the emulator signing-key mismatch blocks visual validation).

- Emulator preview install with `tmp/repack_and_install.py` fails with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`: the currently installed watch face uses a different signing key. Do not uninstall it automatically, since that would lose its configured complications.

- Commit formatting is blocked in the container: `./gradlew spotlessApply` cannot download the required JDK 25 from Foojay; no formatter is configured in the Gradle build. A fallback Black installation also fails because the package index is unreachable.
- Merging the Row 2 slots renumbers Row 3 complication/configuration IDs; existing watch configurations may need to be selected again after installation.

- `local.properties` currently points to `sdk.dir=/Users/niilz/Library/Android/sdk` (macOS host path), which does not exist inside the Linux devcontainer (`/workspaces/bttf-xml`). Running `./gradlew` tasks that require the Android SDK inside the container will fail unless an Android SDK is installed/mounted in the container or `ANDROID_HOME` is configured.
- `watchface/src/main/AndroidManifest.xml` defaults to `com.google.wear.watchface.format.version = 1` despite `minSdk = 36` / `compileSdk = 37` (which supports up to WFF v4).
