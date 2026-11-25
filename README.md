This is a Kotlin Multiplatform project targeting Android, Desktop (JVM), iOS, Web, built with the [Kotlin Toolchain](https://kotlin-toolchain.org/dev/).

- [/androidApp](./androidApp) contains the Android application.
- [/desktopApp](./desktopApp) contains the desktop (JVM) application.
- [/iosApp](./iosApp) contains the iOS application.
- [/shared](./shared) holds the code shared across your applications — Compose UI, business logic, and platform-specific implementations. [src](./shared/src) is for common code; the sibling `src@<platform>` folders (for example `src@android`) hold code compiled only for the platform named in the folder.
- [/webApp](./webApp) contains the web application, compiled to WebAssembly with Kotlin/Wasm.

The `kotlin` (macOS/Linux) and `kotlin.bat` (Windows) scripts in the project root are self-bootstrapping wrappers for the Kotlin Toolchain: they download the pinned toolchain version on first use, so no separate installation is required. Build the whole project with `./kotlin build`.

### Running

Use the run configurations provided by the run widget in your IDE's toolbar. You can also run each module from the command line:

- Android app: `./kotlin run -m androidApp`
- Desktop app: `./kotlin run -m desktopApp`
- iOS app: `./kotlin run -m iosApp`
- Web app: `./kotlin run -m webApp`

### Testing

Run the project's tests with `./kotlin test`, or `./kotlin test -m <module>` for a single module.

The backend's sarf (root-extraction) evaluation methodology, measured numbers and raw run outputs are documented in [docs/evaluation/sarf-baseline.md](./docs/evaluation/sarf-baseline.md).

### Demo data

With the backend dependencies installed and the Quran corpus ingested, create or refresh the demo learner from `backend/`:

```bash
uv run python ../scripts/seed_demo.py
```

The script prints the login:

- Email: `demo@jawhar.app`
- Password: `JawharDemo123!`

It creates a beginner learning path with completed lessons and quizzes, two decks of real Quranic words, SRS cards and two weeks of review history. It refuses to run against a database URL that looks like production and only replaces the demo account's own data on reruns.

---

Learn more about [Kotlin Multiplatform](https://www.jetbrains.com/help/kotlin-multiplatform-dev/get-started.html), [Kotlin Toolchain](https://kotlin-toolchain.org/dev/), [Compose Multiplatform](https://kotlinlang.org/compose-multiplatform/), [Kotlin/Wasm](https://kotl.in/wasm/).
