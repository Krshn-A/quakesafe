# How QuakeSafe is tested

## The plan in one table

| Layer | Question it answers | How | Size | Runs |
|---|---|---|---|---|
| Built-in checks | Is each method and formula right? | `verify()` inside the solver: exact formulas, hand calculations, second methods | 87 checks | In the page (Verify tab) and in `test_solver.py` |
| Regression | Does every page call work, and do fixed bugs stay fixed? | Each call through `api`, one test per bug, the corners of the slider ranges | 253 checks, 25 s | `test_solver.py` |
| Accuracy | How many digits are right? | Each method and model formula against LAPACK, closed forms and second implementations; prints worst error and its limit | 93 checks, 1 min | `test_accuracy.py` |
| Checks on the checks | Would the built-in checks notice a wrong solver? | 56 copies of the solver, each with one deliberate mistake | 56 copies, 2 min | `test_mutants.py` |
| Page wiring | Do the script and the markup agree? | Static checks of `index.html` | 6 checks | `test_solver.py`, section 7 |
| The page in a browser | Does it load, draw and respond? | By hand, with the checklist below | 5 min | Before each release |

```
python test_solver.py
python test_accuracy.py
python test_mutants.py
```

Each needs only Python and numpy, ends with a count of failures and exits with code 1 if there are any. All three run on GitHub for every push and pull request.

## Why it is shaped this way

All the numerical work is Python, and each test script pulls that Python out of `index.html`, so the code that is tested is the code that ships. A wrong period or drift is the worst thing this page can do, so that is where the tests are thickest.

Three decisions shape the rest:

- **Outside truth.** The solver may not call `numpy.linalg`; the tests may. Two hand-written methods that agree can share a mistake, so `test_accuracy.py` compares with LAPACK, with closed-form answers and with second implementations written inside the test (see [ADR-0004](adr/0004-accuracy-is-measured-against-outside-references.md)).
- **Limits that follow the problem.** A linear solve is judged against (condition number × machine epsilon), which is the best any method can do for that matrix, not against a fixed tolerance. A tolerance fixed by hand is either too tight for a 40-storey wall or too loose for an 8-storey frame.
- **Checks that can fail.** A check that would still pass with a wrong formula is worth nothing. `test_mutants.py` proves that each formula in the model is pinned down by at least one built-in check. When the audit of November 2026 began, the built-in checks caught only 10 of 44 deliberately wrong copies.

The page script is JavaScript inside the same file, with no build step, so it cannot be loaded by a JavaScript test runner (see [ADR-0001](adr/0001-one-file-no-build-step.md)). Two things stand in for unit tests there: the static checks of section 7 of `test_solver.py`, and the manual checklist below.

## What each script covers

**`test_solver.py`**

| Section | Example |
|---|---|
| 1. Built-in checks | Code load of a two-storey building worked out by hand, to 1e-12 |
| 2. Referee | Three lowest frequencies of an isolated frame + core building with a damper, against `numpy.linalg.eigvals` |
| 3. Tuning rule | Den Hartog's damping rule against a brute-force search |
| 4. Page calls | `analyse`, `race`, `euler`, `det` on a 1-storey, a 40-storey, a wall, a frame + core, a braced, a damped and a soft-storey building |
| 5. Fixed bugs | A station 48 km from the earthquake is marked "too close" instead of being given 58.8 km |
| 6. Slider corners | 40-storey wall with the weakest core: no NaN, modes in order, no Python exception from any design call |
| 7. Page wiring | Every element the script looks up exists; the README's count of built-in checks equals the real count |

In sections 5 and 6 a reply counts as a crash if its error text starts with a Python exception name, such as `ValueError:`. A plain sentence is a valid answer. All three scripts turn numpy's `RuntimeWarning` into an error, so an overflow or a division by zero inside the solver fails the run.

**`test_accuracy.py`** has eleven sections: direct solvers, iterative solvers, eigenvalues, roots, statistics and regression, Euler, the building model, the static check, the design solves, detection, and the bridge to the page. Its output is the table in [ACCURACY.md](ACCURACY.md).

**`test_mutants.py`** lists each deliberate mistake as a piece of the solver's text and its replacement. If the solver is edited at that spot the entry goes "stale" and the script fails until the entry is updated.

## Adding a test

- **A new numerical method or formula:** add a `chk(...)` line to `verify()` in the solver with a hand-calculated answer, so the page shows it too. Update the count in the README (a test checks it). Add one wrong version of the new code to `test_mutants.py` and see that the new check catches it. Add a line to `test_accuracy.py` if there is an outside reference to measure against.
- **A new call for the page:** add it to the `calls` list in section 4 of `test_solver.py`.
- **A bug:** first add a line to section 5 of `test_solver.py` that fails, then fix the bug.

## Manual browser checklist

Do this in a browser at 100% zoom, and once more on a phone or with the browser's phone view. It takes about five minutes.

**Start-up**

- [ ] The status line at the top right goes from "Loading Python…" to "Ready", and the building appears with its three headline numbers and a pass or fail box.
- [ ] The browser console shows no errors.

**Building**

- [ ] Drag *Storeys* from end to end. The page stays smooth and the drawing follows.
- [ ] Leave the page on this tab for ten seconds. The drawing keeps its size. (On a high-resolution screen it used to grow.)
- [ ] Open *Edit one floor*, pick a floor, change its mass, then reduce *Storeys* below that floor. The floor list goes back to *None*.
- [ ] *Find the minimum stiffness that passes*, then *Apply*. The verdict turns to a pass just under 100%. Move any slider: the sentence under the button disappears.
- [ ] With *Storeys* at 1, *Mode 2* and *Mode 3* are greyed out.
- [ ] Choose *Wall or core*. The column stiffness and bracing controls grey out, and a note says why.

**Shake**

- [ ] Tick the damper, press *Design the damper mass*. A message appears, with the damper's weight in tonnes, and the peak of the curve drops.
- [ ] Set damping to 1% and press it again. The message says the smallest damper already beats the target.
- [ ] Tick base isolation and press *Design the isolator*. The message states the stiffness needed and the stiffness applied, and the natural period is close to the target.
- [ ] *Pin this curve*, change something, and both curves are drawn.

**Detect**

- [ ] Click the map. The star moves and the latitude and longitude boxes follow.
- [ ] Set magnitude to 3. The result says it needs 3 stations with both picks.
- [ ] Set the threshold to 2. The first alert reads "false alarm" and the warning column says so too.
- [ ] Type latitude 24.6 and longitude 54.8. Abu Dhabi's estimate reads "too close".
- [ ] Upload a small CSV. Its trace replaces the synthetic one and stays while other sliders move. Picking a station brings the synthetic recording back.
- [ ] *Estimate stiffness loss* with a period of 60 gives a sentence, not a Python error.

**The link between the tabs**

- [ ] On the Detect tab, raise the magnitude. "Ground shaking there" and "Roof sway of your building" both grow, and the note under the Building tab's answer changes too.
- [ ] Press *Shake the building with this earthquake*. The Shake tab opens with its strength slider locked and a note naming the earthquake. Untick the box: the slider is back at 0.05.
- [ ] On the Building and Shake tabs, the building leans further when a slider makes the sway larger, and swings faster at a higher frequency.

**Lab**

- [ ] Opening the tab fills all eight charts and the table without pressing anything. No legend runs off its chart.
- [ ] Go to the Building tab, change the mass, come back. The cards are worked out again for the new building.
- [ ] Resize the window. The charts are redrawn sharp, not stretched.

**Verify**

- [ ] *Run all checks* reports that every check passed.

**Everywhere**

- [ ] Switch the system between light and dark. Charts change colour with the page.
- [ ] Use Tab and the arrow keys only. Every tab and control can be reached, the focus ring is always visible, and a headline button moves the focus to the tab it opens.
- [ ] Reload with `#lab` at the end of the address. The Lab tab opens.
- [ ] Turn the network off and reload with an empty cache. A box explains that Python could not load and offers *Try again*.

## Colour contrast

Every text colour was checked against every background it sits on, in both colour schemes, by computing WCAG contrast ratios. After the changes of November 2026 the lowest text ratio is 4.8 to 1 in the light scheme and 5.4 to 1 in the dark one (4.5 is required), and input borders and slider rails reach at least 3.3 to 1 (3 is required). If a colour variable at the top of the style sheet is changed, the ratios must be worked out again.

## What is not tested

- **The page script, automatically.** The checklist is manual. Two random-interaction runs in a browser (548 and 421 actions, about three minutes each, checking for errors, stale results, stale sentences and broken layout after each burst) were done by hand on 27 November 2026, before and after the page script was reworked. Both found nothing, but they are not part of the repository. The next step is one browser test (Playwright) that loads the page, waits for "Ready", clicks through the tabs, runs the verification and fails on any console error. It is item 3 in [TECH_DEBT.md](TECH_DEBT.md).
- **The motion-sensor recording**, on a real phone.
- **Opening the file straight from disk** (`file://`).
- **Browsers other than Chromium.** Firefox and Safari have not been checked since the worker was added.
- **Speed.** There is no test that fails if an analysis becomes slow. The times in [ARCHITECTURE.md](ARCHITECTURE.md) section 6 are the reference.
- **Screen readers.** Names, roles and live regions were checked in the markup; nobody has listened to the page.
