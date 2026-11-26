# How QuakeSafe is tested

## The plan in one table

| Layer | What it protects | How | Runs |
|---|---|---|---|
| Numerical methods | Each solver gives the right answer | 50 checks inside the solver (`verify()`), against exact formulas, hand cases and second methods | In the page (tab 5) and in `test_solver.py` |
| Referee | The hand-written methods agree with a trusted library | `numpy.linalg` on random matrices and on a full building model | `test_solver.py` |
| Page calls | Every call the page can make returns an answer, for every kind of building | Each call through `api`, on 8 building types | `test_solver.py` |
| Fixed bugs | Bugs that were found do not come back | One test per bug | `test_solver.py` |
| Slider corners | The extreme ends of the sliders do not crash or give NaN | 9 corner buildings, 5 calls each | `test_solver.py` |
| Page wiring | The script and the markup agree | Static checks of `index.html` | `test_solver.py` |
| The page in a browser | It loads, draws and responds | By hand, with the checklist below | Before each release |

`test_solver.py` has about 175 checks and takes about 20 seconds. It needs only Python and numpy. It runs on GitHub for every push and pull request.

```
python test_solver.py
```

The last line is the number of failures, and the exit code is 1 if there are any.

## Why it is shaped this way

All the numerical work is Python, and the Python is pulled out of `index.html` by the test script, so the code that is tested is the code that ships. That is where most bugs would do real harm (a wrong period or drift), so that is where most tests are.

The page script is JavaScript inside the same file, with no build step, so it cannot be loaded by a JavaScript test runner (see [ADR-0001](adr/0001-one-file-no-build-step.md)). Two things stand in for unit tests there:

- **Static checks.** Section 7 of the test script reads `index.html` as text and checks that every element the script looks up exists, every slider has a starting value, every solver call exists in `api`, every control has a label, and every canvas gives its height as `data-h`.
- **The manual checklist** below.

## What each section of `test_solver.py` covers

| Section | Example |
|---|---|
| 1. Verification suite | Frequencies of a uniform 8-storey frame against the closed-form formula, to 1e-8 |
| 2. Referee | Three lowest frequencies of an isolated frame + core building with a damper, against `numpy.linalg.eigvals` |
| 3. Tuning rule | Den Hartog's damping rule against a brute-force search |
| 4. Page calls | `analyse`, `race`, `euler`, `det` on a 1-storey, a 40-storey, a wall, a frame + core, a braced, a damped and a soft-storey building |
| 5. Fixed bugs | Damper design with an easy target returns the smallest damper instead of "not reachable" |
| 6. Slider corners | 40-storey wall with the weakest core: no NaN, modes in order, no Python exception from any design call |
| 7. Page wiring | The README's count of verification checks equals the real count |

In sections 5 and 6 a reply counts as a crash if its error text starts with a Python exception name, such as `ValueError:`. A plain sentence is a valid answer.

The script turns numpy's `RuntimeWarning` into an error, so an overflow or a division by zero inside the solver fails the run.

## Adding a test

- **A new numerical method:** add a `chk(...)` line to `verify()` in the solver, so the page shows it too. Update the count in the README (a test checks it).
- **A new call for the page:** add it to the `calls` list in section 4.
- **A bug:** first add a line to section 5 that fails, then fix the bug.

## Manual browser checklist

Do this in a browser at 100% zoom, and once more on a phone or with the browser's phone view. It takes about five minutes.

**Start-up**

- [ ] The status pill goes from "Loading Python…" to "Ready", and the building appears.
- [ ] The browser console shows no errors.

**Tab 1 · Building**

- [ ] Drag *Storeys* from end to end. The page stays smooth and the drawing follows.
- [ ] Leave the page on tab 1 for ten seconds. The drawing keeps its size. (On a high-resolution screen it used to grow.)
- [ ] Pick a floor in *Edit one floor*, change its mass, then reduce *Storeys* below that floor. The floor list goes back to *None*.
- [ ] *Find the minimum stiffness that passes*, then *Apply*. *Worst drift ÷ limit* is just under 1.
- [ ] With *Storeys* at 1, *Mode 2* and *Mode 3* are greyed out.

**Tab 2 · Shake test**

- [ ] Tick the damper, press *Design the damper mass*. A message appears and the peak of the curve drops.
- [ ] Set damping to 1% and press it again. The message says the smallest damper already beats the target.
- [ ] Tick base isolation and press *Design the isolator*. The first period is close to the target.
- [ ] *Pin this curve*, change something, and both curves are drawn.

**Tab 3 · Detect**

- [ ] Click the map. The star moves and the latitude and longitude boxes follow.
- [ ] Set magnitude to 3. The result says it needs 3 stations with both picks.
- [ ] Upload a small CSV. A trace is drawn, or a clear message appears.
- [ ] *Estimate stiffness loss* with a period of 60 gives a sentence, not a Python error.

**Tab 4 · Numerics lab**

- [ ] *Run all* fills all eight charts and the table.
- [ ] Go to tab 1, change the mass, come back. A red note says the building has changed.
- [ ] Resize the window. The charts are redrawn sharp, not stretched.

**Tab 5 · Verify**

- [ ] *Run all checks* reports that every check passed.

**Everywhere**

- [ ] Switch the system between light and dark. Charts change colour with the page.
- [ ] Use Tab and the arrow keys only. Every tab and control can be reached.
- [ ] Reload with `#lab` at the end of the address. Tab 4 opens.
- [ ] Turn the network off and reload with an empty cache. A box explains that Python could not load and offers *Try again*.

## What is not tested

- **The page script, automatically.** The checklist is manual. The next step is one browser test (Playwright) that loads the page, waits for "Ready", clicks through the tabs, runs the verification and fails on any console error. It is item 3 in [TECH_DEBT.md](TECH_DEBT.md).
- **The motion-sensor recording**, on a real phone.
- **Opening the file straight from disk** (`file://`).
- **Browsers other than Chromium.** Firefox and Safari have not been checked since the worker was added.
- **Speed.** There is no test that fails if an analysis becomes slow. The times in [ARCHITECTURE.md](ARCHITECTURE.md) section 6 are the reference.
