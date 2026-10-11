# Verification record

Baseline: newly created public `vermakkrish/ManiPool`, clean `main`, initial commit `ef081fe99c6976e08495df86e98c09856aa5a872`, containing README and Node `.gitignore`. No application, dependency manifest, CI or baseline tests existed.

## Observed local results

| Check | Result |
| --- | --- |
| npm dependency install / lockfile install | Passed (`npm ci --ignore-scripts` on Node 24.11.1, npm 11.6.2) |
| `npm run typecheck` | Passed |
| `npm run lint` | Passed, zero warnings |
| `npm test -- --runInBand` | Passed: 17 tests, 2 suites |
| `npm run bundle:android` | Passed: Android production JavaScript bundle + 19 assets |
| Native `assembleDebug` | Environment blocked before project compilation: Gradle loopback connection failure |
| ADB / emulator | Environment blocked: Android preferences directory initialisation failure; no device walkthrough claimed |
| `git diff --check` | Passed before delivery |

The interaction test renders the actual app/navigation with mocked native components and presses through welcome, demo profile, matching, match details, explicit acceptance, vehicle choice/booking confirmation, start/completion and history. Pure tests verify the domain edge cases described in README. Renderer tests do not verify native Android views, date-picker dialogs, keyboard behaviour, real sharing, screenshots, accessibility services or small-device layout.

Metro reports a feature-flags subpath export fallback from the installed upstream React Native dependency graph; it still successfully generates the bundle. No warning suppression or vendor patch was introduced.

Native builds were attempted with Android Studio's JDK 25 and a downloaded Microsoft JDK 17, Gradle 9.4.1, and the installed Android SDK path. Both failed at local loopback initialisation. This is an execution-environment limitation, not evidence that the application's native build passes. The GitHub Actions Android job is a further verification route; its outcome is separate from these local results.

Non-breaking npm audit fixes were attempted. The final local install reports 53 inherited dependency advisories (48 high, 5 moderate), primarily propagated `braces` / `sprintf-js` findings in the Metro/Jest/framework tree. Forced audit fixes propose incompatible changes and were not applied. Review upstream patches before production use.

## Device walkthrough still required

- Launch and native date/time selection, invalid and past requests.
- Small-screen spacing, keyboard resize, TalkBack, Android back and activity restoration.
- Location search/saved places/map schematic, pickup selection, messages/quick actions and sharing dialog.
- Normal, two-rider/auto, no-match/recovery, cancellation and reset flows.
- Confirm no live services/permissions/charges and no secrets in native outputs.

The implementation is a local-session prototype; production authentication, backend persistence, routing, realtime messaging, payments, provider integration and push delivery are deliberately outside scope.
