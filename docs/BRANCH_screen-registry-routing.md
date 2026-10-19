# `fix/screen-registry-routing` — what changed and why

**Base:** `master` · **Commits:** 8 · **Tests:** 25 passing (18 new) · **Build:** clean, all targets

Frontend-only. No backend files touched.

---

## The problem this branch fixes

The app was written by an AI that was asked to design *screens*, and it produced a design-review artifact that had been wired directly into the app's router. Three consequences:

1. **Every visual state became a destination.** `ScreenHost` resolved navigation through the same catalogue the designer browsed, so "log in error", "no internet" and "dark mode home" were all valid places the app could navigate to — even though the host screen already rendered those states internally.
2. **State had nowhere to live.** `JNav.stack` was a `List<String>`, so a step *within* a flow (question 2 of 20, flashcard answer revealed) could only be expressed by pushing another destination.
3. **Nothing survived navigation.** There were no state holders anywhere in `shared/src` — zero `ViewModel`, `StateFlow` or `rememberSaveable`. Plain `remember` is disposed the moment a screen leaves the composition, so the reader lost its scroll position and the flashcard review restarted on every trip out.

---

## Commits

| | |
|---|---|
| `d441ca1` | Separate routable screens from the design gallery |
| `2b8065b` | Collapse the placement assessment into one destination |
| `c4d9664` | Collapse the lesson player into one destination |
| `8d363c5` | **Fix:** route `Dest.Placement` / `Dest.Lesson` to their state machines |
| `7748f76` | **Fix:** make "Review answers" start at question 1 |
| `525d395` | Keep reader and review state across navigation |
| `d32d850` | Adopt Material 3 Expressive spring physics |
| `2e50e44` | **Fix:** drop the press-scale, keep the shape morph |

The three marked `Fix` are bugs I introduced and caught during review. `8d363c5` is the one that shipped broken once: I pointed the routable entries at the gallery preview functions, whose buttons have no-op callbacks, so *Start assessment* and *Start lesson* did nothing.

---

## What it changes

**Routing.** `ScreenSpec` gained a `real` flag. 37 of 88 entries are `real = false` — state variants, dark-mode previews, `wordPopup`, and the dead pager states. The app resolves through `Screens.real` (51 entries); the gallery still shows all 88.

**Navigation.** The stack is now `List<Route(dest, arg)>`. Screens carry data with them instead of writing to a global — `AppState.activeSurahId` is gone, the reader reads its surah from `nav.currentArg`. Also fixed two real bugs: `StateScreens` used `reset()` to change tabs, which clears the crossfade flag, so those animated as push slides.

**Flows.** Placement and lesson were each N destinations with hardcoded progress labels ("7 / 20", "2 / 5"). Each is now one destination with a step index. Both compute their results from real answers instead of fixed copy — the lesson result had claimed 92% accuracy and a 13-day streak no matter what you answered.

**State.** `nav/RouteState.kt` adds `ScreenSession`, remembered once in `App()` and provided as `LocalSession`. `ReaderState` and `ReviewState` guard on an entry id, so re-entering restores rather than resets.

**Motion.** New `design/Motion.kt` holds the M3 Expressive springs; every animation in the design system now reads from it instead of a hand-picked bezier. Buttons morph shape on press rather than shrinking.

---

## Things a reviewer should push back on

- **The 12 placement questions and 5 lesson questions in `Mock.kt` were written from grammar knowledge, not by a native speaker.** They set a learner's starting level. **They need sign-off before shipping.** No Quranic text or `surah:ayah` citation was invented — the questions are about patterns and case endings only.
- **`JawharMotion.reduced` is never set.** Compose Multiplatform does not expose the platform "remove animations" setting to shared code, so the mechanism is there and unwired. Wire it from the Appearance settings screen.
- **The surah list and vocabulary screens still refetch on every visit.** They do not lose a *position*, so they were left alone.
- **The onboarding decorative loops still use curves, not springs.** Springs cannot repeat forever.

---

## How to check it

```
./kotlin build && ./kotlin test
./kotlin run -m desktopApp
```

Set `AppState.galleryEnabled = true` to browse all 88 states.

- Sign up → placement intro → *Start assessment* → 12 questions → *See my level* → *Review answers* (should start at question 1 and show right/wrong).
- Learn tab → a lesson node → 5 content steps → 5 questions → result. Back should step backwards through the lesson, not exit it.
- Quran tab → open a surah → scroll → tap a word → *Analyse verse* → back. You should return to the same scroll position with the word popup still open.
- Hold a button down. It should change **shape** and colour, not shrink.