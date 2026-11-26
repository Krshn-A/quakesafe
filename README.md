# QuakeSafe

A one-page tool for building sway, earthquake protection and earthquake detection, built for a numerical methods course.

The whole app is `index.html`. The numerical solver is Python, embedded in that file and run in the browser by Pyodide. Every method is written by hand; `numpy` is used only to hold arrays, and no `numpy.linalg` routine is called.

## Host it with GitHub Pages

1. Open this repository on GitHub and go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
3. Choose branch **main** and folder **/ (root)**, then **Save**.
4. After a minute or two the page is live at `https://<your-username>.github.io/quakesafe/`.

The first load takes several seconds while the browser downloads Python.

## What it does

| Tab | Contents |
|---|---|
| 1 · Building | Frame, wall/core or frame + core buildings; soft storeys, uneven mass, bracing; natural periods and mode shapes; code-style static drift check; minimum-stiffness design |
| 2 · Shake test | Damped response to steady shaking across frequencies; tuned mass damper, base isolation and inter-storey dampers; condition number of the undamped system |
| 3 · Detect | Trigger on synthetic recordings; distance from the P-to-S gap; epicentre from station distances; magnitude; warning time per city; damage check from a period change |
| 4 · Numerics lab | Every linear solver on one problem; iterative convergence; SOR relaxation scan; determinant roots; root-finding comparison; Euler error growth; regression |
| 5 · Verify | 47 checks against exact formulas, hand calculations and second methods |
| 6 · Limits and sources | Assumptions, what is synthetic, references |

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

## Run the tests

```
pip install numpy
python test_solver.py
```

The script extracts the solver from `index.html`, so it tests exactly what the page runs. It uses `numpy.linalg` only as a referee.

## What is synthetic or assumed

- Building presets and earthquake load values are illustrative.
- Seismograms are generated, and the magnitude scale is the one used to generate them.
- Only the UOSS station is real; the other stations are hypothetical.
- The regression sample rows are synthetic and should be replaced with measured data.
- The slow-shaking period bands come from a summary of a published study and should be checked against the paper.

See tab 6 in the app for the full list of limits.
