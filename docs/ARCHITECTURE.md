# How QuakeSafe is designed

This is for someone who wants to change the app and needs to know where things are and why they are that way. For what the app does, see the [README](../README.md).

## 1. What the app has to do

**Functions**

- Let a student set up a building with sliders and see its periods, mode shapes and code-style drift check at once.
- Show the steady shaking response and the effect of a roof damper, base isolation and floor dampers.
- Run an earthquake detection pipeline on synthetic recordings, or on the user's own recording.
- Show every numerical method of the course on the same problem, with its convergence.
- Check itself against exact answers, in the page and in a test script.

**Other requirements**

| Requirement | Target | Why |
|---|---|---|
| No server | Static files only | Hosted free on GitHub Pages; nothing to maintain |
| Methods are hand-written | No `numpy.linalg`, no SciPy | Course rule; the test script enforces it |
| The solver can be read and tested on its own | Ordinary Python, in the page source | The numerical methods are the point of the project |
| Sliders feel live | Page never freezes; result within about 2 s for the largest building | A frozen page looks broken |
| Works on a phone and on high-resolution screens | 360 px wide and up, any pixel ratio | A link gets opened on whatever device the reader has |
| One person can maintain it | No build step, no packages | Course project |

**Size of the problem.** One user, one building at a time. At most 40 storeys, so matrices are at most 42 × 42 (84 × 84 for the damped system). There is no stored data and no account. Scale is not a concern; clarity and correctness are.

## 2. The parts

```
 index.html
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  PAGE (markup + styles)            PAGE SCRIPT (JavaScript, main thread)   │
│  six tabs, sliders, tables,  ◄───► state S, mMul, kMul ── params() ──┐     │
│  16 canvases                       render*, plot, drawBuilding       │     │
│                                         ▲                            │     │
│                                         │ result (JSON text)         │     │
│                                         │                            ▼     │
│                                    ┌────┴───────────────────────────────┐  │
│                                    │ solver link: call(name, args)      │  │
│                                    │ one request at a time, in order    │  │
│                                    └────┬───────────────────────────▲───┘  │
│  - - - - - - - - - - - - - - - - - - - -│- - - postMessage - - - - -│- - - │
│                                         ▼                           │      │
│  WORKER (background thread)        api(name, json) ─────────────────┘      │
│  Pyodide = Python in WebAssembly   ┌────────────────────────────────────┐  │
│                                    │ SOLVER (Python, hand-written)      │  │
│                                    │ linear solvers · eigenvalues ·     │  │
│                                    │ roots · regression · Euler ·       │  │
│                                    │ building model · detection · verify│  │
│                                    └────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
        ▲ downloaded once, then cached by the browser
        │
 cdn.jsdelivr.net/pyodide/v0.27.7  (Python runtime + numpy, about 9 MB)
```

| Part | Lives in | Knows about |
|---|---|---|
| Page | top of `index.html` | Nothing. Elements are found by `id`. |
| Solver | `<script type="text/python" id="solver">` | Numbers only. No page, no JavaScript. Runs unchanged in plain Python, which is how `test_solver.py` tests it. |
| Worker | `<script type="text/js-worker" id="worker">` | How to load Pyodide and pass one call to `api`. |
| Page script | last `<script>` | The page, the state, and the names of the solver calls. |

The solver never touches the page and the page script never does any numerical method. The one exception to watch for is small display arithmetic in the page script (unit conversions, evaluating the fitted curve `C·hˣ` for the chart).

## 3. What happens when a slider moves

1. The `input` event writes the new value into the state object `S` and updates the number beside the slider.
2. `refresh()` waits 120 ms for the slider to settle, then asks for an analysis.
3. `params()` turns the state into SI units. The solver link sends `{name: "analyse", payload}` to the worker.
4. In the worker, Python's `api("analyse", payload)` runs the model and returns one JSON string.
5. The reply becomes `R`, the latest result. `renderAll()` fills the tables and charts from it. The building drawing is animated from `R` on every frame.

If more slider events arrive while an analysis is running, they do not queue up. They collapse into one more run with the newest values (`latest()` in the page script). Detection works the same way with its own result `DET`.

Buttons (design, calibrate, run the lab, verify) send their own calls. A button is locked while its call runs.

## 4. The door between the page and the solver

Everything goes through one Python function:

```python
api(name: str, payload: str) -> str      # JSON in, JSON out
```

- A problem the user can cause comes back as `{"error": "plain words"}` and the page shows the words.
- An exception inside the solver is caught in `api` and comes back as `{"error": "ValueError: ..."}`. The page shows it in the status line of the header. The tests treat any such message as a bug.
- NaN and infinity cannot travel in JSON. `_clean` turns them into `null`, and rounds every number to 7 significant figures.
- An iteration that was cut off at its cap says so with a `capped` flag (mode search, the three root finders in the stiffness design, power iteration). The page prints it beside the step count.

**The building, `p`** (all SI units):

| Field | Meaning |
|---|---|
| `N`, `h` | storeys, storey height (m) |
| `m[]`, `k[]` | mass of each floor (kg), stiffness of each storey (N/m) |
| `system`, `EI` | `"frame"`, `"wall"` or `"dual"`; core bending stiffness (N·m²) |
| `zeta`, `ag` | structural damping ratio; ground shaking (g) |
| `brace`, `iso`, `tmd`, `visc` | optional devices, each `{on, ...}` |
| `code` | load settings `{SDS, SD1, R, Cd, I, drift}` |
| `npts`, `cond` | sweep resolution; whether to compute condition numbers |

**The calls**

| Call | Argument | Returns | Used by |
|---|---|---|---|
| `analyse` | `p` | modes, static check, frequency sweep, warnings, the structure's own `K` scaled to 1 | Building and Shake tabs, on every change |
| `design_stiffness` | `p` | stiffness multiplier by bisection, false position, fixed point, each with `capped` | Building tab button, lab |
| `design_tmd` | `{p, target}` | damper mass ratio, tuning, `smallest` flag | Shake tab button |
| `design_isolation` | `{p, T}` | isolator stiffness | Shake tab button |
| `tmd_rule` | `{mu}` | textbook tuning and damping | Shake tab button |
| `detect` | quake, stations, cities, settings | picks, distances, epicentre or `epi_note`, warning times; per station `too_close` and `false_trigger`; `false_alarm` | Detect tab, on every change |
| `record` | `{x, fs, t?, thr?}` | picks on the user's own recording | Detect tab upload and sensor |
| `damage` | `{p, T}` | stiffness kept | Detect tab button |
| `race` | `p` | every linear solver on the static problem | lab |
| `det` | `p` | determinant curve and its roots | lab |
| `euler` | `p` | energy and roof motion for three step sizes | lab |
| `regression` | `{h[], T[]}` | power-law fit and hold-out error | lab |
| `calibrate` | `{p, T}` | stiffness multiplier that gives period `T` | lab button |
| `verify` | none | the list of self-checks | Verify tab, test script |
| `seismometer` | `{f0, zeta, freqs}` | response of a mass-on-spring sensor | verification only |

To add a feature: write the Python function, add one line to `api`, call it from the page script with `solver.call` (errors are an expected answer) or `solver.must` (an error is a bug). `test_solver.py` fails if the page calls a name that `api` does not have.

## 5. Drawing

- Charts are drawn on `<canvas>` by one function, `plot`. There is no chart library.
- A canvas states its height in CSS pixels as `data-h`. `prep()` sets the bitmap to that size times the screen's pixel ratio. The height must not be read back from the `height` attribute, which holds the bitmap size; doing that made every chart grow on each redraw on high-resolution screens.
- Each chart remembers how to draw itself (`retained`). `redrawVisible()` replays the visible ones when a tab is opened, the window is resized or the fonts arrive. Nothing is drawn into a hidden canvas.
- Colours are CSS variables. A series colour such as `"--acc"` is looked up at drawing time, so a chart always has the colours of the page.
- The look ("Midnight", since 28 November 2026) is set by the variables at the top of the style sheet: a near-black navy page, orange `--acc` for the main series and controls, cyan `--acc2` for the second series, green, amber and red for safe, close and failing. The page is dark only; it does not follow the system's light or dark setting. Headlines use Manrope, with one phrase in the accent colour (`.hl`); labels and numbers use DM Mono and body text DM Sans, all from Google Fonts with system fonts as fall-back. Tabs, buttons and badges are pill-shaped. Text on a canvas uses `FONT(px)`. Charts drawn before the fonts arrive are redrawn when they do.
- The building drawing is a sketch: storeys are drawn as leaning panels with lit windows, the roof slab is orange, and a glowing trace runs along the hatched ground. The windows (which ones are lit never changes), the glow (`glow()`) and the trace on the Building tab are decoration, and so is the trace behind each tab's headline. The sway, the storey colours, the slab and column thicknesses (mass and stiffness multipliers) and the labels come from the solver.
- The two building drawings are animated. They become still pictures when the system asks for reduced motion.

## 6. How long things take

Measured in a Chromium browser on a laptop, on 26 November 2026:

| Call | 8-storey frame | 40-storey frame + core |
|---|---|---|
| `analyse` | 0.37 s | 1.8 s |
| `design_stiffness` | 0.06 s | 0.5 s |
| `race` (lab) | 0.13 s | 1.3 s |
| `detect` | 0.12 s | same |
| `verify` | 2.5 s | same |

Most of `analyse` is the frequency sweep: about 190 frequencies, each with one Gauss elimination of the damped system and one Gauss–Jordan inverse for the condition number. A phone is several times slower.

Because the solver is in a worker, these times do not block the page. Dragging the storeys slider from 9 to 40 on a frame + core building gave a longest pause of 18 ms on the main thread. Before the worker, each step of that drag froze the page for up to 1.8 s.

## 7. What can go wrong, and what the page does

| Failure | What the user sees |
|---|---|
| Pyodide cannot be downloaded (offline, CDN blocked) | A box at the top with the reason and a **Try again** button; solver buttons stay locked |
| The worker stops | The same box; waiting calls are cancelled |
| A design target cannot be met | The reason in plain words under the button |
| An exception inside the solver | `Error: ...` in the status line; the previous result stays on screen |
| NaN or infinity in a result | Shown as "–"; charts skip the point |
| A drawing function throws | Logged to the console; the animation keeps running |
| The worker dies without a word (browsers can kill one) | After five minutes with no answer, the same box as for a stopped worker |
| A design answer arrives after the sliders moved | Nothing is applied; a sentence says so |
| A result sentence no longer matches the sliders | It is cleared at the next analysis |
| A bad recording file | A message under the upload button |

## 8. Choices and their costs

The reasons are written up one decision at a time in [adr/](adr/):

1. [One file, no build step](adr/0001-one-file-no-build-step.md)
2. [The solver runs in a web worker](adr/0002-solver-in-a-web-worker.md)
3. [One JSON door between the page and the solver](adr/0003-one-json-door.md)
4. [Accuracy is measured against outside references, in a script of its own](adr/0004-accuracy-is-measured-against-outside-references.md)

How accurate the numbers are, method by method, is in [ACCURACY.md](ACCURACY.md).

## 9. What to look at again if the app grows

- **More than about 2 s per analysis** (more storeys, finer sweep): compute the sweep in two passes, coarse while the slider moves and fine when it stops, or drop the condition-number curve from the live path.
- **More JavaScript** (roughly past 1,000 lines): move the page script into its own files with a small test runner. That ends the one-file rule, so update ADR 1.
- **Use without internet**: add a service worker that keeps Pyodide. A service worker must be its own file, so the same ADR applies.
- **Sharing a set-up**: put the state `S` in the address, as the tab already is.
- **Real recordings**: the detection constants (window lengths, wave speeds) are fixed in the solver; they would need to become inputs.
