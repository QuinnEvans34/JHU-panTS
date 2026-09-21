# UI test foundation — September 20, 2026

**Result:** Scoped build/unit/synthetic-browser foundation passed. Not full UI/G0/G7 qualification.

## Scope and preservation

Quinton authorized the unchanged UI baseline and initial test foundation, not a redesign or
case-package migration. No production component, CSS, Vite build config, or hosting script changed.
No external drive, real-image browser session, inference service, deployment, or Plan 04 code was used.
The unchanged build copies existing local demo assets into ignored `ui/dist`; they were not viewed,
uploaded, or repurposed as test fixtures. The fixture server disables `publicDir` and replaces the
NiiVue import only in its isolated test configuration. Its screenshots explicitly show a viewer stub.

Previous `ui/dist` and `ui/node_modules` were moved intact into ignored
`outputs/prowl/testing/ui-foundation-2026-09-20/prior-dist` and `prior-node_modules` before the first
clean install. Baseline package/lock copies and all run logs remain there as well. No files were
deleted for this preservation step; these relocated dependencies are historical evidence, not the
active environment. New test source directories are `ui/tests`, `ui/tests/fixtures`, and
`ui/tests/browser`. Playwright browser binaries were installed in its normal user cache.

## Environment and dependency evidence

- macOS 27.0, Apple Silicon; Node **24.21.0**, npm **11.19.0**. Node was installed through the
  existing nvm installation and checksum-verified. `ui/.nvmrc` pins the project version; shells must
  explicitly select it. Other projects need not change their Node version.
- Existing package versions were all preserved, including React 18.3.1, NiiVue 0.69.0, Vite 5.4.21,
  and React Vite plugin 4.7.0. A lock comparison found **zero changed pre-existing package versions**.
- Added exact test pins: Vitest 3.2.7, React Testing Library 16.3.3, DOM Testing Library 10.4.2,
  user-event 14.6.7, jsdom 30.1.0, Playwright 1.63.0. Vitest 3 supports the existing Vite 5 family;
  this intentionally avoids an unreviewed Vite major upgrade. See
  [Vitest 3 prerequisites](https://v3.vitest.dev/guide/).
- Chromium: Chrome for Testing 153.0.8010.12, Playwright build 1243.
- Original lock SHA-256: `65b8f4ab80d0f3658ce2c2e94ded531f55cfe4d78d359bdf9b1769a8c1f58963`.
- Updated lock SHA-256: `8730a1f34eb551974e8e79f65557ab32ec1df61a9e79159870de8607626524ac`.

## Reproduce from the repository

```sh
cd ui
nvm use
npm ci
npm run test:run
npx --no-install playwright install chromium
npm run test:e2e
npm run build
```

`nvm use` requires nvm initialized in the shell; install the pinned version first if absent.
Browser tests start their own loopback-only fixture server on port 5179, refuse to reuse a server,
and stop it afterward. Unit tests reject fetch calls. Browser tests block unexpected origins and
case requests; the historical Google Fonts CSS request receives an explicit local empty response.
Thus screenshots use fallback fonts and are not pixel-identical production-font baselines.
`test:fixture` is an interactive test-only preview; it is not the application demo or a deployment.
Preserve browser artifacts before reruns when failures matter: Playwright replaces its output folder.

## Results and retained first failures

| Check | Result |
|---|---|
| Clean install from original lock | Passed |
| Unchanged production build | Passed, 1.50 seconds reported by Vite |
| Clean install with test dependencies | Passed |
| Unit/helpers/component tests | 18 passed, approximately 0.71 seconds |
| Chromium synthetic control flow | 1 passed, 1.8 seconds including startup |
| Production build after test additions | Passed, 1.14 seconds reported by Vite |
| Source/build-config preservation | No diff in `ui/src`, `ui/vite.config.js`, or `ui/scripts` |
| Formatting | `git diff --check` passed |

Coverage includes initial display state, case reset, arrival of a live prediction without resetting
display settings, evidence/source distinction, immutable layer toggles, selection/reset behavior,
locked evidence controls, 2D/3D switching, drawer state, and one keyboard-activated settings control.
It does not prove prediction quality, spatial alignment, durable review persistence, or real rendering.

First unit run: 17 passed/1 failed because the new test incorrectly expected the drawer to be removed
from the DOM. Existing CSS collapses it instead. The test was corrected without application changes.
Browser attempts exposed three test-fixture issues, retained in logs/traces/screenshots:
1. An opacity-zero drawer does not satisfy Playwright's hidden-element assertion; assertions now
   check its existing opacity/pointer-event behavior, not claim accessibility hiding.
2. A partial accessible-name match also found “Close view settings”; an exact-name locator fixed it.
3. The production CSS requested Google Fonts; the fixture now explicitly stubs that stylesheet.

Logs: `baseline-install.log`, `baseline-build.log`, `test-dependencies.log`, `unit-first.log`,
`clean-test-install.log`, `unit-verified.log`, `build-verified.log`, `browser-first.log`,
`browser-verified.log` (second failed attempt despite the provisional filename), `browser-final.log`
(third failed attempt), and `browser-pass.log` inside the dated evidence folder.
Failed browser artifacts are preserved under `browser-first-artifacts`, `browser-second-artifacts`,
and `browser-third-artifacts` there. Latest screenshots are under `outputs/prowl/testing/ui-browser/`.

## Visual evidence and remaining work

Captured synthetic screenshots at 1440×900, 1280×720, and 1024×768. Inspected 1440 and 1024 images:
existing controls and empty viewer layout render; the stub text is partly overlapped by floating
controls, as expected of this diagnostic placeholder. No design changes were made. Full tab-order,
focus visibility, 200% browser zoom, axe accessibility checks, real NiiVue/WebGL, source alignment,
and positive/negative/false-positive case baselines remain open. In particular, collapsed drawer
controls may remain focusable: assess separately rather than claiming accessibility from opacity.

The historical offline-copy promise about cached predictions is displayed, not tested. The fixture
does not exercise inference, the full App loader, review storage, or reference reveal after prediction.
Full G0 still needs its remaining contract/environment evidence; G7 is not closed by this slice.

## Dependency and build follow-ups

`npm audit` returned **8 advisories: 3 high, 5 moderate**, zero critical, in the combined toolchain.
Affected packages: Vite, Vitest, @vitest/mocker, esbuild, browserslist, baseline-browser-mapping,
nanoid, and postcss. Machine-readable details are retained in `npm-audit.json`. No automatic audit
fix or major upgrade was performed. Triage reachability and a compatible upgrade plan separately;
this is not security approval for hosting the development server or deploying the application.
Servers in this work were loopback-only. Tests are non-watch runs.

Build warnings about chunks over 500 kB remain. npm also warned about esbuild/fsevents install-script
approval coverage; no blanket permission change was made. Browser runner emitted color-environment
warnings. These warnings are retained rather than suppressed.

Next approved work: additional contract/metric tests, one bounded task at a time. Production UI
migration, full browser/accessibility qualification, and dependency remediation remain separate.
