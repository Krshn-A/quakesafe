# Known weak points

A list of what is still weak in QuakeSafe, highest priority first. Last reviewed 27 November 2026, after an accuracy audit of the solver and a second review of the page.

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
| 3 | No automated browser test. Page-script bugs are caught only by hand. Two reviews of the page script found about twenty display and wording defects that no test could have seen. | Test | 3 | 4 | 3 | 21 |
| 4 | Only Chromium has been tried. Firefox and Safari differ in sliders, workers and canvas text. | Test | 2 | 3 | 2 | 20 |
| 5 | No licence file. Nobody else is legally allowed to reuse the code. | Docs | 1 | 2 | 1 | 15 |
| 6 | Pyodide is fetched from one CDN at run time, with no integrity check (a worker cannot use one) and no copy in the repository. If the CDN is down or blocked, the page cannot start. | Dependency | 2 | 3 | 3 | 15 |
| 7 | Pyodide is pinned at 0.27.7. Nothing prompts an update. | Dependency | 1 | 2 | 1 | 15 |
| 8 | The page script has no unit tests and cannot have any while it is inline (ADR-0001). | Test | 2 | 3 | 3 | 15 |
| 9 | The code-style check leaves out the long-period branch, the extra lower bound on the load for sites with S₁ ≥ 0.6 g (leaving it out is on the unsafe side there), and the second soft-storey rule. The page says so. | Model | 2 | 3 | 3 | 15 |
| 10 | A set-up cannot be shared. Only the tab is in the address, not the building. | Feature | 2 | 1 | 2 | 12 |
| 11 | On a phone the drawing is below the sliders, so the effect of a slider is off screen. | Design | 2 | 1 | 2 | 12 |
| 12 | The three typefaces are fetched from Google Fonts on every first visit: one more outside service, and a request that tells Google the page was opened. Keeping the font files beside the page would end both, but the app would no longer be one file. | Dependency | 1 | 2 | 2 | 12 |
| 13 | `drawBuilding` and `drawMap` are long functions with many statements per line. They work, but they are slow to read and change. | Code | 2 | 1 | 2 | 12 |
| 14 | Nobody has listened to the page with a screen reader. Names, roles and live regions are in the markup; the verdict box is re-announced after every analysis, which may be too talkative. | Test | 1 | 2 | 2 | 12 |
| 15 | Result sentences under the regression buttons are not cleared when the building changes (the others are). | Code | 1 | 1 | 1 | 10 |
| 16 | One analysis of a 40-storey building takes about 1.8 s (several times more on a phone). The page does not freeze, but the result lags the slider. | Speed | 2 | 1 | 3 | 9 |
| 17 | Power iteration is cut off at 5000 steps for about 1 building in 100, leaving 5 good figures. It is only used for a number in the Lab's text, and the text says when it happened. | Numerics | 1 | 1 | 2 | 8 |
| 19 | The formula that links the Detect tab's earthquake to the building (`site_shaking`, added 28 November 2026) is checked by hand values in `test_solver.py` only. It has no row in the page's 87 built-in checks and no wrong copy in `test_mutants.py`, because the presentation quotes 87. Move the checks into `verify()` after it. | Test | 2 | 2 | 1 | 20 |
| 20 | That link is rough: one harmonic S wave at 1 Hz, read as a Wood-Anderson trace, with a distance correction made for Southern California. It gives an order of magnitude. A published ground-motion relation for the region would be better. | Model | 1 | 2 | 3 | 9 |
| 18 | Arrival picks are up to about 1 s late and stations nearer than about 55 km give no distance, because of the trigger's fixed windows (1 s, and 7 s between P and S). Shorter windows would need retuning against false triggers. | Model | 1 | 1 | 3 | 6 |

## Suggested order

**Now (an hour or two in total)**

- Item 1: open the live page on a phone, go through the checklist in [TESTING.md](TESTING.md), and try the motion-sensor button. Then remove the "has not been tested on a phone" line from the Limits tab, or fix what breaks.
- Item 4: open the live page in Firefox, and in Safari if a Mac or an iPhone is at hand, and go through the same checklist.
- Item 5: choose a licence and add the file.
- Item 7: make checking the Pyodide version a once-a-term job. After a change, repeat the browser comparison in [ACCURACY.md](ACCURACY.md) section 5.

**Next (a day or two)**

- Item 3: one Playwright test that loads the page, waits for "Ready", opens each tab, presses *Run all checks*, and fails on any console error. Add it to the GitHub workflow as a second job. A random-interaction run like the one described in TESTING.md would be a good second test.
- Item 2: replace the regression rows with measured periods (Goel and Chopra 1997) and check the period bands against the paper.

**Later, only if the project keeps growing**

- Items 8 and 13 together: move the page script into its own file, split the two long drawing functions, add unit tests for `fmt`, `ticks`, `parseRows` and `latest`. This ends the one-file rule, so update ADR-0001 first.
- Item 6: keep a copy of Pyodide beside the page, or add a service worker.
- Item 9: add the two missing branches of the code check, each with a hand calculation in `verify()` and a wrong copy in `test_mutants.py`.
- The rest as time allows.

## Fixed in the audit of 27 November 2026

Solver (measured before and after in [ACCURACY.md](ACCURACY.md), section 3):

| Was | Now |
|---|---|
| A wall's stiffness matrix was slightly lopsided after inversion, and Cholesky read only half of it: a 40-storey wall's sway was good to 5 figures. | The matrix is made symmetric: 10 figures. |
| A station 44 to 55 km from the earthquake was given 58.8 km whatever the truth. | It is refused as "too close". |
| At a low threshold, noise set off an alert before the earthquake and the page showed impossible warning times. | Labelled a false alarm; no warning times shown. |
| The root finders' sign test multiplied two values and could underflow. | They compare signs. |
| Jacobi's and SOR's divergence guard could never fire. | It watches the size of the answer. |
| A matrix singular to rounding was solved without complaint. | It is refused. |
| Iterations cut off at their cap looked like any other. | Each is flagged, in the solver and on the page. |
| The lab's "work" column counted direct and iterative solvers differently. | One way of counting. |
| 50 built-in checks, several unable to fail; they caught 10 of 44 deliberately wrong solvers. | 87 checks; they catch 55 of 56. |

Page:

| Was | Now |
|---|---|
| Chart legends ran off the right edge on most screens. | Legends wrap onto a second line and long names are cut with an ellipsis. |
| The zero tick of an axis could read "-1.39e-17". | Ticks are exact multiples of the step. |
| Long axis numbers lost their minus sign off the left edge. | The left margin grows to fit the longest number. |
| In a wall-only building the column, bracing and storey-stiffness controls did nothing, and the design result quoted a column stiffness that is not in the model. | The controls are switched off with a note, and the result is about the core. |
| The isolator design claimed a period that the applied, rounded stiffness did not give (1.99 s for a target of 5 s in one case). | The slider moves in steps of 0.1, and the message states what is needed and what was applied. |
| PASS and FAIL in the calculation trail were grey. | Green and red. |
| The damper block stayed on the centre line while the roof swayed, and in mode shapes it took all the movement. | It rides on the roof; the drawing is scaled to the building. |
| City labels overlapped on the map. | Each label sits on the side that is clear. |
| An uploaded recording's text stayed while the charts went back to the synthetic one; the same file could not be chosen twice. | The upload stays on the charts until a station is picked, and is analysed again when the threshold or sample rate changes. |
| Numbers of 100,000 and more lost their requested precision. | They keep it. |
| The preset still named itself after bracing or a device was switched on. | It reads "Custom". |
| Sentences under the design buttons stayed after the building changed. | They are cleared when they no longer apply. |
| Five pairs of text and background colour were below the 4.5 to 1 contrast required; input borders and slider rails were below 3 to 1. | All pass, in both colour schemes. |
| Headline buttons hid the element that had the keyboard focus; results under buttons were not announced; tables that scroll could not be reached by keyboard. | Focus moves to the new tab; results are live regions; scrolling tables are focusable. |
| Google Fonts could hold the page up while its style sheet loaded. | It loads without blocking. |
| A worker killed by the browser left the page on "Computing…" for ever. | After five minutes without an answer the page says the solver has stopped and offers to restart it. |

## Fixed in the review of 26 November 2026

Charts growing on high-resolution screens; the page freezing on every solver call; the damper design's wrong "not reachable"; raw Python errors; Euler overflow; stale floor selection; no message when Python failed to load; no labels or keyboard access; no CI. See the commit of that date.
