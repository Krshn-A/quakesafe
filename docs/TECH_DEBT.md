# Known weak points

A list of what is still weak in QuakeSafe, highest priority first. Last reviewed 26 November 2026.

Each item is scored 1 to 5 on three things:

- **Impact:** how much it slows work down or hurts users now.
- **Risk:** how bad it is if it is left alone.
- **Effort:** how hard the fix is (1 = an hour, 5 = weeks).

Priority = (Impact + Risk) × (6 − Effort). A higher number means do it sooner.

## Open items

| # | Item | Kind | Impact | Risk | Effort | Priority |
|---|---|---|---|---|---|---|
| 1 | Never run on a real phone. The motion-sensor recording is untested, and the worker has only been run in Chromium on a laptop (with a phone-sized window). | Test | 2 | 4 | 1 | 30 |
| 2 | Placeholder data. The regression rows are synthetic and the slow-shaking period bands come from a summary, not the paper. Both are labelled in the page, but any conclusion drawn from them is not backed by data. | Data | 3 | 3 | 2 | 24 |
| 3 | No automated browser test. Page-script bugs are caught only by hand. The worst bug found so far (charts growing on high-resolution screens) was in the page script, and no test that existed could have seen it. | Test | 3 | 4 | 3 | 21 |
| 4 | No licence file. Nobody else is legally allowed to reuse the code. | Docs | 1 | 2 | 1 | 15 |
| 5 | Pyodide is fetched from one CDN at run time, with no integrity check (a worker cannot use one) and no copy in the repository. If the CDN is down or blocked, the page cannot start. | Dependency | 2 | 3 | 3 | 15 |
| 6 | Pyodide is pinned at 0.27.7. Nothing prompts an update. | Dependency | 1 | 2 | 1 | 15 |
| 7 | The page script has no unit tests and cannot have any while it is inline (ADR-0001). | Test | 2 | 3 | 3 | 15 |
| 8 | A set-up cannot be shared. Only the tab is in the address, not the building. | Feature | 2 | 1 | 2 | 12 |
| 9 | On a phone the drawing is below the sliders, so the effect of a slider is off screen. | Design | 2 | 1 | 2 | 12 |
| 10 | Wall stiffness is made by inverting a flexibility matrix. For 40 storeys the static residual is about 1e-5 instead of 1e-13. The page states this. | Numerics | 2 | 2 | 3 | 12 |
| 11 | `drawBuilding` and `drawMap` are long functions with many statements per line. They work, but they are slow to read and change. | Code | 2 | 1 | 2 | 12 |
| 12 | One analysis of a 40-storey building takes about 1.8 s (several times more on a phone). The page no longer freezes, but the result lags the slider. | Speed | 2 | 1 | 3 | 9 |
| 13 | If the browser itself kills the worker (for example when memory runs out), no event reaches the page: the status stays on "Computing…" and no retry is offered until the page is reloaded. | Code | 1 | 2 | 2 | 12 |
| 14 | The three typefaces are fetched from Google Fonts on every first visit: one more outside service, and a request that tells Google the page was opened. Keeping the font files beside the page would end both, but the app would no longer be one file. | Dependency | 1 | 2 | 2 | 12 |
| 15 | City labels overlap on the map (Dubai and Sharjah). | Design | 1 | 1 | 2 | 8 |

## Suggested order

**Now (an hour or two in total)**

- Item 1: open the live page on a phone, go through the checklist in [TESTING.md](TESTING.md), and try the motion-sensor button. Then remove the "has not been tested on a phone" line from the Limits tab, or fix what breaks.
- Item 4: choose a licence and add the file.
- Item 6: make checking the Pyodide version a once-a-term job.

**Next (a day or two)**

- Item 3: one Playwright test that loads the page, waits for "Ready", opens each tab, presses *Run all* and *Run all checks*, and fails on any console error. Add it to the GitHub workflow as a second job.
- Item 2: replace the regression rows with measured periods (Goel and Chopra 1997) and check the period bands against the paper.

**Later, only if the project keeps growing**

- Items 7 and 11 together: move the page script into its own file, split the two long drawing functions, add unit tests for `fmt`, `ticks`, `parseRows` and `latest`. This ends the one-file rule, so update ADR-0001 first.
- Item 5: keep a copy of Pyodide beside the page, or add a service worker.
- Items 8, 9, 10, 12, 13, 14 and 15 as time allows.

## Fixed in the November 2026 review

| Was | Now |
|---|---|
| Every chart grew taller each time it was redrawn on any screen whose pixel ratio is not 1 (phones, most laptops). The animated building drawings became unusable within a second. | Height comes from `data-h`; a test forbids a `height` attribute on a canvas. |
| Every solver call froze the page (up to 1.8 s per slider step). | Solver runs in a worker; longest pause measured 18 ms. |
| Detection ran on every slider event with no delay. | Waits for the slider to settle and collapses repeated requests. |
| Damper design said "not reachable" when even the smallest damper beat the target. | Returns the smallest damper and says so. |
| The peak used by the damper design was read from a 45-point scan. At 0.5% damping that scan read only 66% of the true peak (87% at 1%). | The scan is refined around its highest point; checked against a 3001-point scan. |
| Raw Python errors reached the user (`ValueError: no sign change in the bracket`, `matrix is not positive definite`, `division by zero`). | Each case returns a plain sentence; a test looks for exception names in replies. |
| Euler's method overflowed to infinity on tall buildings and left gaps in the charts. | A run stops once its energy passes 1e30. |
| The damage check showed an "exact answer" that is wrong when bracing is on. | The exact value is shown only when it applies. |
| A failed analysis after a design button left the page with a broken result, and one error in a drawing stopped the animation for good. | Errors are checked in one place; the animation loop survives an error. |
| After reducing the storeys, the editor still showed a floor that no longer existed. | The selection is cleared. |
| Lab and design charts were stretched after a window resize and kept old colours after a light/dark switch. | Every chart redraws itself. |
| If Pyodide failed to load, the only sign was "loadPyodide is not defined". | A message with the reason and a retry button. |
| Sliders had no labels for screen readers, tabs had no roles, floors could only be picked with a mouse, the earthquake could only be moved by clicking. | Labels, tab roles and arrow keys, a floor list, latitude and longitude boxes, text descriptions on charts, still pictures for reduced motion. |
| `test_solver.py` only worked from the repository folder, and there was no CI. | Works from anywhere; runs on GitHub for every push. |
| No design notes; the README did not say how to run the page locally. | README, ARCHITECTURE, TESTING and three decision records. |
