# How accurate QuakeSafe's numbers are

Measured on 27 November 2026 with `python test_accuracy.py`. Every number in this file comes from that script, from `test_mutants.py`, or from the browser comparison described in section 5. Run them again after any change to the solver; if a number here no longer matches, this file is out of date.

**In short:** every hand-written method agrees with LAPACK or a closed-form answer to within a few rounding units of the best a computer can do for that problem. The periods are right to 8 figures and the static sway to at least 9, including for a 40-storey wall. What limits the accuracy of the page is not the arithmetic but four modelling choices, all listed in section 2: the trigger's one-second window, the flat map, the stopping rules of the iterative methods, and the simplified code check.

## 1. Each method against an outside reference

"Rounding units" means the error divided by (condition number × machine epsilon). That product is the best accuracy any solver can promise for that matrix, so a value near 1 means "as good as possible". The solver itself may not call `numpy.linalg`; the tests may, and do.

| Method | Checked against | Cases | Worst error |
|---|---|---|---|
| Gauss elimination with pivoting | LAPACK, random matrices of 1 to 60 unknowns, a third needing a row swap | 72 | 0.23 rounding units |
| LU decomposition and solve | LAPACK; L·U rebuilt and compared with the row-swapped matrix | 72 | 0.23 rounding units |
| Determinant from LU | LAPACK | 72 | relative 5e-13 or better (60 unknowns) |
| Gauss–Jordan inverse | LAPACK; A·A⁻¹ against the identity | 72 | 0.38 rounding units |
| Condition number (row-sum norm) | LAPACK | 72 | 0.22 rounding units |
| Cholesky and its solve | LAPACK; L·Lᵀ rebuilt | 66 | 1.1 rounding units |
| Thomas algorithm, up to 200 unknowns | LAPACK | 66 | 0.23 rounding units |
| 8 × 8 Hilbert matrix (condition number 3e10) | known answer | 2 | 0.02 rounding units |
| Rows that differ in size by up to 1e14 | planted answers; LAPACK on the same systems | 56 | 7.5e-13, against LAPACK's 3.3e-13; none refused as singular |
| Jacobi, Gauss–Seidel, SOR run to convergence | LAPACK | 15 | 7e-11 |
| Inverse iteration, three lowest eigenvalues | LAPACK `eigh`, 120 random buildings with isolation, dampers and bracing | 360 | 7e-9 |
| Inverse iteration, mode shapes | LAPACK, angle between the two | 360 | 1 − cos = 3e-9 |
| Inverse iteration, two nearly equal eigenvalues (lightly tuned damper) | LAPACK | 9 | 5e-9 |
| Power iteration, highest eigenvalue | LAPACK | 120 | 2e-5 (see section 2) |
| Bisection | known roots of five functions | 5 | 0.74 of the tolerance asked for |
| False position, fixed-point iteration (run to convergence) | known roots | 6 | 3e-12 |
| Mean, sample standard deviation | numpy | 40 | 5e-16 |
| Linear interpolation, including both ends of the table | `numpy.interp` | 480 | 2e-16 |
| Least squares (normal equations + Cholesky) | LAPACK `lstsq` | 40 | 1e-15 |
| Power-law fit and its r² | `numpy.polyfit` in log–log space; r² from its definition | 80 | 2e-13 |
| Euler's method, the time loop | the exact Euler recurrence, mode by mode | 6 | 5e-14 |
| Euler's method, order of accuracy | halving the step | 3 | measured order 0.998 (should be 1) |
| Building model: mass, stiffness, damping matrices | a second assembly written inside the test, in other coordinates | 120 | 7e-10 |
| Wall flexibility formula | numerical unit-load integral | 3 | 1e-11 |
| Damping matrix | damping ratio of mode 1 read from the eigenvalues of the first-order system | 4 | 3e-12 |
| Steady shaking response | complex-number solve by LAPACK, one frequency on a resonance | 480 | 0.32 rounding units |
| Steady shaking response, the physics | Runge–Kutta time integration over 60 periods | 1 | 2e-5 (the integrator's own error) |
| Shake test as sent to the page | complex solve on the second assembly | 160 | 6e-9 |
| Shake test at the corners of the slider ranges (softest isolator, stiffest core, lightest damper with no dashpot) | complex-number solve by LAPACK | 576, from 192 buildings | 0.29 rounding units; none refused |
| Code-style static check: Cs, storey forces | a second calculation written inside the test; all four branches of the Cs rule reached | 120 | 5e-16 |
| Static sway and drift ÷ limit | LAPACK on the same matrix | 120 | 0.30 rounding units |
| Static sway of walls up to 40 storeys | flexibility × load, which needs no inverse | 12 | 2e-10 |
| Isolator design, calibration, damage factor | period from the second assembly; (period ratio)² | 120 | 4e-8 |
| Stiffness design by three root finders | drift ÷ limit = 1 at the answer, and agreement between them | 40 | 1e-5 |
| Two-mass damper response | closed-form solution of the two equations | 30 | 2e-15 |
| Damper tuning rule | brute-force search over 16,653 dampers for the lowest peak | 3 mass ratios | the rule's own point was the best on the grid |
| Damper design by bisection | the sway left, re-measured with a 4001-point scan | 4 | 0.0002 of the peak |
| STA/LTA | direct window-by-window calculation | 581 | 4e-14 |
| Epicentre from exact distances | the planted point | 200 | 0.56 rounding units |
| Resampling | `numpy.interp` | 592 | 1e-16 |
| Warning time | its definition, from the true distance | 18 | exact |
| Magnitude distance correction | Hutton and Boore's published formula | 5 | exact |

## 2. Limits that are not rounding

These are properties of the methods and the model. Each is stated on the page (Limits tab) and, where it applies, beside the number it affects.

| What | Size | Why | Where the page says so |
|---|---|---|---|
| P and S picks are late | P up to 0.85 s, S up to 0.55 s, never early (magnitude 5 to 7, 70 to 900 km) | The trigger averages over a 1 s window, which has to fill | Limits tab; "P pick late" column |
| Distance from the P-to-S gap | within 4.6 km for 70 to 900 km | Follows from the pick lateness | Station table shows true and estimate |
| A station nearer than about 55 km gives no distance | none of 225 recordings at 30 to 54 km gave one; at 55 km 6 of 9 did; from 56 km all do. Just beyond the limit the distance always reads long, by up to 5.5 km | The S search can only start 7 s after the P pick, and the P pick is itself a little late | "too close" in the station table; Limits tab |
| Low trigger thresholds fire on noise | with 90 s of quiet before the P wave: 27 of 30 recordings trigger early at threshold 2, 1 of 30 at threshold 3, none at 4 or 5. Ten times the noise gives the same counts, because the trigger is a ratio | A ratio of short to long average of pure noise fluctuates | "false trigger" and "false alarm" labels |
| Flat map against the round Earth | distances up to 4.0% off at the corners of the map | One fixed scale for longitude | Limits tab |
| Magnitude reads low | by 0.025 | The synthetic wave train never quite reaches its nominal height | Limits tab |
| Iterative solvers stop on their last step, not their error | Gauss–Seidel stopped at 1e-7 was 730 times further from the answer | A slow iteration takes small steps while still far away | Lab tab, note under the table and its last column |
| False position and fixed-point iteration can hit their cap | fixed-point uses all 300 steps when bracing carries most of the load | The update removes only a small part of the error each time | "stopped at its cap" beside the step count |
| Power iteration is cut off at 5000 steps | 1 building in 120; the answer is then good to 5 figures instead of 10 | The two highest eigenvalues are almost equal | Lab tab text |
| A lumped wall against a smooth beam | first frequency 9.1%, 4.8%, 2.4%, 1.2% low for 10, 20, 40, 80 storeys | A whole floor's mass sits at the roof; a smooth beam has half of one there | Limits tab ("Floors are lumped masses") |
| The damper's mass comes from the solver's own mode shape | 3.5e-6 | A mode shape is known less precisely than its frequency | none; too small to show |
| Numbers reach the page with 7 significant figures | 3.6e-7 | Rounding in the bridge keeps the messages small | ARCHITECTURE.md |
| The code check is simplified | no long-period branch, no extra lower bound for S₁ ≥ 0.6 g, one soft-storey rule of two | Scope of a course project | Limits tab |

## 3. What the audit changed

| Was | Now | Measured |
|---|---|---|
| The wall's stiffness matrix came out of the inverse slightly lopsided (6e-11 of its size) and Cholesky read only half of it | The matrix is made exactly symmetric | 40-storey wall: sway error 4e-6 → 2e-10; residual shown on the page 3e-5 → 9e-10 |
| A station 44 to 55 km away had its S pick pinned 7 s after the P pick | It gives no distance and the table says "too close" | It used to report 58.8 km whatever the truth, up to 15 km off |
| At a low threshold a trigger on noise produced an alert before the earthquake and "warning times" longer than the wave's travel time | The alert is labelled a false alarm and no warning times are shown | At threshold 2 the first alert came 14 s before the earthquake began |
| The root finders tested for a sign change by multiplying two function values | They compare signs | For values near 1e-200 bisection returned 0 instead of the root. Not reachable from the sliders: across their extremes no determinant came anywhere near that small |
| Jacobi's and SOR's divergence test compared a relative step with 1e12 and so could never fire | It watches the size of the answer | A diverging 2 × 2 problem ran 573 sweeps into overflow; now 24 |
| Gauss elimination called a matrix singular only if a pivot was exactly zero | A pivot below 1e-14 of the largest entry of its own row counts as zero | [[1,2,3],[4,5,6],[7,8,9]] with a right-hand side of ones used to return [−2.5, 4, −1.5] with no error; the matrix has no inverse |
| The first version of that rule compared each pivot with the largest entry of the whole matrix (a mistake of the audit itself, found by its second review) | Each pivot is compared with its own row, and one refused point no longer stops a whole shake test | It refused 48 of 6,144 sound buildings at the corners of the sliders, where a concrete core sits beside the spring of a 0.2% damper. Now 0 of 192 in the test |
| The peak used by the damper design came from a 45-point scan (fixed on 26 November) | The scan is refined around its top | At 0.5% damping the scan read 66% of the true peak |
| The lab's "work" column counted every operation for direct solvers but only multiplications for iterative ones | One way of counting for all | Next to the iterative solvers, the direct ones looked about twice as dear as they are |
| Iterations cut off at their cap were reported like any other | Each says so | — |
| The page's built-in checks had tolerances far looser than the errors (2% of an 80 s arrival time; 6% on a wall frequency) and five that could not fail | 87 checks, with tolerances near what is achieved and a hand calculation behind each formula | Section 4 |

## 4. Would the checks notice a wrong solver?

A check that always passes proves nothing. To test the checks, `test_mutants.py` makes 56 copies of the solver, each with one deliberate mistake (a dropped factor of g, cos instead of cos², a flipped sign, a wrong exponent, no pivoting, a natural log for a log to base 10, and so on) and runs the page's own `verify()` on each.

| Checks | Wrong copies caught |
|---|---|
| The 50 built-in checks before the audit | 10 of the first 44 |
| The whole of `test_solver.py` before the audit | 18 of the first 44 |
| The 87 built-in checks now | **55 of 56** |

The one that is not caught removes a second, redundant clean-up step in inverse iteration and gives the same results to every figure checked, so it is not a mistake that could be noticed.

## 5. The browser gives the same numbers

The tests run in desktop Python (3.14, numpy 2.5). The page runs Pyodide (Python 3.12, numpy 2.0, compiled to WebAssembly). Four buildings, the detection pipeline and every `verify()` value were computed in both and compared:

| Compared | Largest difference |
|---|---|
| Periods, drift ÷ limit, roof sway, sweep peak, condition number, design multiplier (apartment, 30-storey tower, 40-storey wall, 12 storeys with every device) | none in the 7 figures the page receives |
| Sum of all response shapes over the sweep | 1e-9 |
| Station distances, magnitude, warning times | none |
| The built-in checks | all pass in both; largest difference in any computed value 3e-15 |

Repeat this whenever the Pyodide version changes (see [DEPLOY.md](DEPLOY.md)).

## 6. Repeating the measurements

```
python test_accuracy.py     # about a minute; prints one line per row of section 1
python test_mutants.py      # about two minutes; prints one line per wrong copy
```

Both exit with code 1 if anything is outside its limit, and both run on GitHub for every push.
