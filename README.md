# QuakeSafe

A one-page tool for building sway, earthquake protection and earthquake detection, built for a numerical methods course.

**Live page:** https://krshn-a.github.io/quakesafe/

The whole app is `index.html`. The numerical solver is Python, embedded in that file and run in the browser by Pyodide. Every method is written by hand; `numpy` is used only to hold arrays, and no `numpy.linalg` routine is called.

## What it does

| Tab | Contents |
|---|---|
| Building | Frame, wall/core or frame + core buildings; soft storeys, uneven mass, bracing; natural periods and mode shapes; code-style static drift check; minimum-stiffness design |
| Shake | Damped response to steady shaking across frequencies; tuned mass damper, base isolation and inter-storey dampers; condition number of the undamped system; the strength can be taken from the Detect tab's earthquake |
| Detect | Trigger on synthetic recordings; distance from the P-to-S gap; epicentre from station distances; magnitude; warning time per city; what the earthquake does to the building where it stands; damage check from a period change |
| Lab | Every linear solver on one problem; iterative convergence; SOR relaxation scan; determinant roots; root-finding comparison; Euler error growth; regression. It fills itself for the building on screen |
| Verify | 87 checks against exact formulas, hand calculations and second methods |
| Limits | Assumptions, what is synthetic, references |

A tab can be linked directly: add `#shake`, `#detect`, `#lab`, `#verify` or `#about` to the address.

The tabs share one building and one earthquake. A change on one tab shows on the others: the building's sliders move the Shake curves, the Lab and the "At the building" lines of the Detect tab; the earthquake's magnitude and position give a ground shaking under the building, which the Shake tab can use as its strength.

## Methods and where they are used

| Method | Job |
|---|---|
| Gauss elimination with partial pivoting | Damped shaking response (a non-symmetric system of twice the size) |
| LU decomposition | Reused at every step of inverse iteration; determinant |
| Gauss–Jordan inverse | Wall stiffness from its flexibility matrix; condition numbers |
| Cholesky | Static sway of wall and dual buildings; regression normal equations |
| Thomas algorithm | Static sway of frame buildings (tridiagonal) |
| Jacobi, Gauss–Seidel, SOR | Comparison on the static problem, with a relaxation-factor scan |
| Power and inverse power iteration | Highest and lowest natural frequencies |
| Condition number | Soft storeys, resonance spikes, station geometry |
| Bisection | Design stiffness, damper mass, isolator stiffness, calibration, damage factor, determinant roots |
| False position, fixed-point iteration | Design stiffness, compared with bisection |
| Linear regression | Period-against-height power law; epicentre with more than three stations |
| Interpolation | Code load height exponent; resampling uneven recordings |
| Mean and standard deviation | Detection trigger; magnitude across stations; hold-out error |
| Euler's method | Free vibration, showing energy growth and round-off |

## Run it on your own computer

Serve the folder with any web server. Python has one built in:

```
python -m http.server 8000
```

Then open http://localhost:8000. The first load takes several seconds while the browser downloads Python (about 9 MB from cdn.jsdelivr.net); after that the browser keeps it. The three typefaces come from Google Fonts; without them the page falls back to system fonts.

There is nothing to install and nothing to build. To change the app, edit `index.html` and reload. (Opening the file by double-clicking it has not been tested; use the server.)

## Run the tests

```
pip install numpy
python test_solver.py
```

The script extracts the solver from `index.html`, so it tests exactly what the page runs. It uses `numpy.linalg` only as a referee. It also checks that the page and its script agree (for example, that every element the script looks up exists).

Two more scripts go further:

```
python test_accuracy.py     # how many digits are right, method by method, against LAPACK and closed forms
python test_mutants.py      # would the built-in checks notice a wrong solver? 56 deliberate mistakes
```

All three run on GitHub for every push and pull request (`.github/workflows/tests.yml`).

- [docs/ACCURACY.md](docs/ACCURACY.md) gives the measured accuracy of every method and the limits that are not rounding.
- [docs/TESTING.md](docs/TESTING.md) says what is tested, what is not, and lists the checks to do by hand in a browser.

## How it is put together

`index.html` has three parts:

| Part | Where | Job |
|---|---|---|
| Page | the markup and styles at the top | Six tabs of sliders, tables and charts |
| Solver | `<script type="text/python" id="solver">` | All the numerical methods and the models, in Python |
| Page script | the last `<script>` | Keeps the sliders' values, asks the solver for results, draws them |

The solver runs in a background thread (a web worker), so the page does not freeze while it computes. The page script and the solver talk through one function, `api(name, json)`.

- [docs/QuakeSafe-Study-Guide.pdf](docs/QuakeSafe-Study-Guide.pdf) is a short study guide: the site from zero, every method, and viva questions.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) explains the design, the list of solver calls and the known failure cases.
- [docs/adr/](docs/adr/) records the four main design decisions and why they were made.
- [docs/TECH_DEBT.md](docs/TECH_DEBT.md) lists what is still weak, in order of priority.
- [docs/DEPLOY.md](docs/DEPLOY.md) is the checklist for putting a new version live.

## Host it with GitHub Pages

1. Open this repository on GitHub and go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
3. Choose branch **main** and folder **/ (root)**, then **Save**.
4. After a minute or two the page is live at `https://<your-username>.github.io/quakesafe/`.

## What is synthetic or assumed

- Building presets and earthquake load values are illustrative.
- Seismograms are generated, and the magnitude scale is the one used to generate them.
- Only the UOSS station is real; the other stations are hypothetical.
- The regression sample rows are synthetic and should be replaced with measured data.
- The slow-shaking period bands come from a summary of a published study and should be checked against the paper.

See the Limits tab in the app for the full list.

## Files

```
index.html                    the whole app: page, Python solver, page script
test_solver.py                does every call work, and do fixed bugs stay fixed
test_accuracy.py              how accurate each method is, against outside references
test_mutants.py               do the built-in checks catch a wrong solver
README.md                     this file
docs/ARCHITECTURE.md          how the app is designed
docs/ACCURACY.md              measured accuracy, method by method
docs/TESTING.md               test plan and the manual browser checklist
docs/DEPLOY.md                checklist for putting a new version live
docs/TECH_DEBT.md             known weak points, in priority order
docs/adr/                     design decisions and the reasons for them
.github/workflows/tests.yml   runs the three test scripts on GitHub
```
