# ADR-0004: Accuracy is measured against outside references, in a script of its own

**Status:** Accepted
**Date:** 2026-11-27
**Deciders:** project author

## Context

The solver's rule is that every numerical method is written by hand and no `numpy.linalg` routine is called. That rule says how the code must be written. It does not say how anyone can know the hand-written code is right.

Until now two things checked it. `verify()` inside the solver compares it with closed-form answers and with itself (LU against Gauss, bisection against inverse iteration). `test_solver.py` adds a handful of comparisons with `numpy.linalg` and checks that nothing crashes. Both answer "does it pass?", with tolerances chosen by hand. Neither says how many digits are right, and several tolerances were loose enough to hide real loss of accuracy: a 40-storey wall's static sway was good to only five figures, and the check for it allowed 6% on a related quantity.

## Decision

Keep three layers, each with one job:

1. **`verify()` in the solver** stays small and self-contained. It runs in the browser, so it can only use what the solver may use.
2. **`test_solver.py`** stays the regression suite: every page call works, fixed bugs stay fixed, the page's wiring is consistent.
3. **`test_accuracy.py`** (new) measures error. For each method and each model formula it runs many cases against a reference the solver is not allowed to use: LAPACK through `numpy.linalg`, closed-form solutions, and second implementations written inside the test (a direct assembly of the building, a Runge-Kutta time integration, a code-load calculation, a great-circle distance). It prints the worst error next to the limit it is held to.

Errors of linear solves are judged against (condition number × machine epsilon), which is the best any method can do, instead of against a fixed tolerance. [ACCURACY.md](../ACCURACY.md) is written from this script's output.

## Options considered

### Option A: only self-checks inside the solver

| Dimension | Assessment |
|---|---|
| Complexity | Lowest |
| Cost | None |
| Scalability | Poor: a method and its check can share one mistake |
| Team familiarity | High |

**Pros:** visible in the page; obeys the no-library rule everywhere.
**Cons:** two hand-written methods that agree can both be wrong; no outside truth for ill-conditioned cases.

### Option B: a referee inside the page (load `numpy.linalg` in the browser and show the difference live)

| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Cost | A second code path in the page; more to explain |
| Scalability | Good |
| Team familiarity | Medium |

**Pros:** the marker sees the agreement with LAPACK without running anything.
**Cons:** puts `numpy.linalg` calls in the shipped page, right next to code that promises not to use them; one slip and the solver's rule is broken in the product itself.

### Option C: a separate measuring script outside the page (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Medium: about 400 lines of test code |
| Cost | One more minute of test time |
| Scalability | Good: a new method gets a new line |
| Team familiarity | High |

**Pros:** outside truth; the solver stays clean; the output is an accuracy report; limits scale with the conditioning of each problem.
**Cons:** runs on desktop Python, not in the browser, so it does not by itself prove the browser gives the same numbers.

## Trade-off analysis

Option C's gap is the browser. It is closed in two ways. `verify()` still runs in the browser (tab Verify), and a one-off comparison of four buildings, the detection pipeline and all the `verify()` values between desktop Python and Pyodide found no difference in any of the seven figures the page receives (see ACCURACY.md). Option B would close the same gap permanently but at the price of putting library calls in the page, which is the one thing the course rule exists to prevent.

## Consequences

- A change to the solver now has to keep 93 measured errors within their limits, not just pass.
- The built-in checks grew from 50 to 87, each formula of the model now having a hand calculation behind it. A fourth script, `test_mutants.py`, proves that they bite: it feeds `verify()` 56 solvers with one deliberate mistake each and expects every one to be caught.
- The first run found real problems that the pass/fail tests had let through (see ACCURACY.md, "What the audit changed").
- `numpy.linalg` appears in two files, both tests. `test_solver.py` still fails if the word `linalg` appears in the solver.
- Revisit Option B if the browser's numbers ever disagree with desktop Python, for example after a Pyodide upgrade. The comparison is quick to repeat and is part of the deploy checklist for such a change.

## Action items

1. [x] Write `test_accuracy.py` and run it in the GitHub workflow.
2. [x] Write ACCURACY.md from its output.
3. [ ] Repeat the desktop-against-browser comparison whenever the Pyodide version changes.
