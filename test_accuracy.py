"""Measures how accurate the solver in index.html is, method by method, against independent references.
Run:  python test_accuracy.py      (needs numpy; about a minute)

test_solver.py asks "does it work and stay working". This script asks "how many digits are right".
Every line prints the worst error found over many cases and the limit it is held to, so the output
doubles as an accuracy report (docs/ACCURACY.md is written from it).

References used here, none of which the solver itself may use:
  numpy.linalg (LAPACK), exact closed-form answers, and separate re-implementations written in this file
  (a direct assembly of the building model, an RK4 time integration, a code-load calculation, a great-circle
  distance, a brute-force STA/LTA).
"""
import re, sys, math, json, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
html = (ROOT / "index.html").read_text(encoding="utf-8")
src = re.search(r'<script type="text/python" id="solver">\n(.*?)</script>', html, re.S).group(1)
warnings.simplefilter("error", RuntimeWarning)
S = {}
exec(compile(src, "solver(index.html)", "exec"), S)
EPS = np.finfo(float).eps
rng = np.random.default_rng(20261127)

fails = 0; rows = []
def report(name, worst, limit, cases, note=""):
    """One line of the report. The check passes when the worst error is within the limit."""
    global fails
    ok = bool(worst <= limit)                 # a NaN fails
    fails += (not ok)
    rows.append({"name": name, "worst": float(worst), "limit": float(limit), "cases": int(cases), "ok": ok, "note": note})
    print("%s  %-74s worst %.2e   limit %.0e   (%d cases)%s" % ("PASS" if ok else "FAIL", name, worst, limit, cases, "   " + note if note else ""))

def flag(name, ok, note=""):
    """A yes/no check."""
    global fails
    fails += (not ok)
    rows.append({"name": name, "worst": 0.0 if ok else 1.0, "limit": 0.5, "cases": 1, "ok": bool(ok), "note": note})
    print("%s  %-74s %s" % ("PASS" if ok else "FAIL", name, note))

def relerr(x, ref):
    x = np.asarray(x, float); ref = np.asarray(ref, float)
    return float(np.max(np.abs(x - ref)) / max(float(np.max(np.abs(ref))), 1e-300))

def section(title):
    print("\n--- " + title)

# =====================================================================================================
section("1. direct linear solvers against LAPACK")
SIZES = [1, 2, 3, 5, 8, 13, 21, 34, 60]
def general(n):                                # a random matrix; every third one needs a row swap at the first step
    A = rng.normal(size=(n, n))
    if n > 1 and rng.random() < 0.34:
        A[0, 0] = 0.0
    return A
w = {"gauss": 0, "lu": 0, "lu_rebuild": 0, "det": 0, "inv": 0, "inv_resid": 0, "cond": 0}; cases = 0
for n in SIZES:
    for _ in range(8):
        A = general(n); b = rng.normal(size=n); c = np.linalg.cond(A, np.inf); cases += 1
        ref = np.linalg.solve(A, b)
        # a forward error is judged against (condition number x machine epsilon), the best any solver can promise
        w["gauss"] = max(w["gauss"], relerr(S["gauss_solve"](A, b), ref) / (c * EPS))
        lu = S["lu_decompose"](A); P, perm, sign = lu
        w["lu"] = max(w["lu"], relerr(S["lu_solve"](lu, b), ref) / (c * EPS))
        L = np.tril(P, -1) + np.eye(n); U = np.triu(P)
        w["lu_rebuild"] = max(w["lu_rebuild"], relerr(L @ U, A[perm]) / EPS)
        w["det"] = max(w["det"], abs(S["lu_det"](lu) - np.linalg.det(A)) / abs(np.linalg.det(A)) / (n * EPS * 200))
        inv = S["gauss_jordan_inverse"](A)
        w["inv"] = max(w["inv"], relerr(inv, np.linalg.inv(A)) / (c * EPS))
        w["inv_resid"] = max(w["inv_resid"], float(np.max(np.abs(A @ inv - np.eye(n)))) / (c * EPS))
        w["cond"] = max(w["cond"], abs(S["cond_inf"](A) - c) / c / (c * EPS))
report("Gauss elimination: error / (cond x eps)", w["gauss"], 50, cases, "50 means within 50 rounding units of the best possible")
report("LU solve: error / (cond x eps)", w["lu"], 50, cases)
report("LU factors rebuild the row-swapped matrix: error / eps", w["lu_rebuild"], 200, cases)
report("Determinant from LU: relative error / (200 n eps)", w["det"], 1, cases)
report("Gauss-Jordan inverse: error / (cond x eps)", w["inv"], 50, cases)
report("Gauss-Jordan inverse: |A inv(A) - I| / (cond x eps)", w["inv_resid"], 50, cases)
report("Condition number (row-sum norm): relative error / (cond x eps)", w["cond"], 50, cases)

w = {"chol": 0, "chol_solve": 0, "thomas": 0}; cases = 0
for n in SIZES + [120, 200]:
    for _ in range(6):
        k = rng.uniform(0.2, 5.0, size=n); K = S["frame_matrix"](k); b = rng.normal(size=n); cases += 1     # tridiagonal, positive definite
        c = np.linalg.cond(K, np.inf); ref = np.linalg.solve(K, b)
        e = np.concatenate([[0.0], np.diag(K, -1)]); g = np.concatenate([np.diag(K, 1), [0.0]])
        w["thomas"] = max(w["thomas"], relerr(S["thomas"](e, np.diag(K), g, b), ref) / (c * EPS))
        if n <= 60:
            B = rng.normal(size=(n, n)); A = B @ B.T + n * np.eye(n); c2 = np.linalg.cond(A, np.inf)
            Lc = S["cholesky"](A)
            w["chol"] = max(w["chol"], relerr(Lc @ Lc.T, A) / EPS)
            w["chol_solve"] = max(w["chol_solve"], relerr(S["cholesky_solve"](Lc, b), np.linalg.solve(A, b)) / (c2 * EPS))
report("Cholesky: L L^T rebuilds A: error / eps", w["chol"], 200, cases)
report("Cholesky solve: error / (cond x eps)", w["chol_solve"], 50, cases)
report("Thomas algorithm (up to 200 unknowns): error / (cond x eps)", w["thomas"], 50, cases)

H = np.array([[1.0 / (i + j + 1) for j in range(8)] for i in range(8)]); xh = np.ones(8)       # Hilbert matrix, cond about 3e10
report("Badly conditioned system (8 x 8 Hilbert): Gauss error / (cond x eps)", relerr(S["gauss_solve"](H, H @ xh), xh) / (np.linalg.cond(H, np.inf) * EPS), 50, 1)
report("Badly conditioned system (8 x 8 Hilbert): Cholesky error / (cond x eps)", relerr(S["cholesky_solve"](S["cholesky"](H), H @ xh), xh) / (np.linalg.cond(H, np.inf) * EPS), 50, 1)
sing = np.array([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [1.0, 0.0, 1.0]])
try:
    S["gauss_solve"](sing, [1.0, 2.0, 3.0]); raised = False
except ZeroDivisionError:
    raised = True
flag("A singular matrix is refused by Gauss elimination, given cond = inf and det = 0",
     raised and math.isinf(S["cond_inf"](sing)) and S["lu_det"](S["lu_decompose"](sing)) == 0.0)
try:
    S["cholesky"](np.array([[1.0, 2.0], [2.0, 1.0]])); raised = False
except ValueError:
    raised = True
flag("Cholesky refuses a matrix that is not positive definite", raised)

# =====================================================================================================
rng2 = np.random.default_rng(4); w = wl = wi = 0; cases = 0; refused = 0     # rows that differ in size by up to 1e14: sound, and must not be called singular
for n in (2, 3, 5, 8, 13, 21, 42):
    for _ in range(8):
        G = rng2.normal(size=(n, n)) + n * np.eye(n); D = 10.0 ** rng2.uniform(-7, 7, size=n); A = D[:, None] * G; xt = rng2.normal(size=n); cases += 1
        try:
            x = S["gauss_solve"](A, A @ xt); Ai = S["gauss_jordan_inverse"](A)
        except ZeroDivisionError:
            refused += 1; continue
        c = np.linalg.cond(G, np.inf)                     # the conditioning once every row is brought to the same size
        w = max(w, relerr(x, xt)); wl = max(wl, relerr(np.linalg.solve(A, A @ xt), xt))
        wi = max(wi, float(np.max(np.abs(Ai @ A - np.eye(n)))) / (c * EPS * n))
# Pivoting without first scaling the rows costs accuracy on such a matrix, for LAPACK exactly as for the solver, so LAPACK's own error is the yardstick.
report("Badly scaled rows (sizes 1e-7 to 1e7): Gauss worst error / LAPACK's worst error", w / wl, 5, cases, "solver %.1e, LAPACK %.1e against the planted answers" % (w, wl))
report("Badly scaled rows: inverse x matrix against the identity / (n cond eps)", wi, 50, cases)
flag("None of the badly scaled systems is refused as singular", refused == 0, "%d of %d refused" % (refused, cases))

# =====================================================================================================
section("2. iterative solvers")
w = {"jac": 0, "gs": 0, "sor": 0}; cases = 0; slow = 0.0
for n in (3, 8, 15, 25, 40):
    k = rng.uniform(0.5, 2.0, size=n); K = S["frame_matrix"](k); b = rng.normal(size=n); ref = np.linalg.solve(K, b); cases += 1
    for key, fn in (("jac", lambda: S["jacobi"](K, b, 1e-13, 400000)), ("gs", lambda: S["gauss_seidel"](K, b, 1e-13, 400000)), ("sor", lambda: S["sor"](K, b, 1.6, 1e-13, 400000))):
        x, it, hist = fn()
        w[key] = max(w[key], relerr(x, ref))
    x, it, hist = S["gauss_seidel"](K, b, 1e-7, 400000)          # the stopping rule used on the page
    slow = max(slow, relerr(x, ref) / 1e-7)
report("Jacobi run to convergence: error against LAPACK", w["jac"], 1e-8, cases)
report("Gauss-Seidel run to convergence: error against LAPACK", w["gs"], 1e-8, cases)
report("SOR (omega 1.6) run to convergence: error against LAPACK", w["sor"], 1e-8, cases)
report("Gauss-Seidel stopped at approx. error 1e-7: true error / 1e-7", slow, 1e5, cases,
       "the stopping rule measures the last step, not the distance to the answer")
bad_matrix = np.array([[1.0, 3.0], [4.0, 1.0]])           # not diagonally dominant: Jacobi diverges on it
x, it, hist = S["jacobi"](bad_matrix, np.array([1.0, 1.0]), 1e-8, 5000)
flag("Jacobi gives up early on a diverging problem and never overflows", it < 100 and bool(np.all(np.isfinite(x))), "gave up after %d sweeps" % it)
x, it, hist = S["sor"](S["frame_matrix"]([1.0, 1.0, 1.0]), np.ones(3), 2.3, 1e-8, 5000)
flag("SOR with a relaxation factor above 2 gives up early and never overflows", it < 300 and bool(np.all(np.isfinite(x))), "gave up after %d sweeps" % it)

# =====================================================================================================
section("3. eigenvalues: inverse iteration and power iteration against LAPACK")
def random_building(extreme=False):
    N = int(rng.integers(1, 41)); system = str(rng.choice(["frame", "wall", "dual"]))
    mass = rng.uniform(50, 1000) * 1000; stiff = rng.uniform(20, 2000) * 1e6
    m = [mass * float(rng.choice([0.2, 1, 1, 1, 4])) for _ in range(N)]; k = [stiff * float(rng.choice([0.1, 1, 1, 1, 3])) for _ in range(N)]
    return {"N": N, "h": float(rng.uniform(2.6, 5)), "m": m, "k": k, "system": system, "EI": float(rng.uniform(100, 10000)) * 1e9,
            "zeta": float(rng.uniform(0.005, 0.1)), "ag": 0.05,
            "brace": {"on": bool(rng.random() < 0.3), "A": float(rng.uniform(5, 200)) * 1e-4, "bay": 6},
            "iso": {"on": bool(rng.random() < 0.35), "kb": float(rng.uniform(1, 400)) * 1e6, "mb": mass, "zb": 0.15},
            "tmd": {"on": bool(rng.random() < 0.35), "mu": float(rng.uniform(0.002, 0.15)), "f": float(rng.uniform(0.7, 1.2)), "zd": float(rng.uniform(0, 0.4))},
            "visc": {"on": bool(rng.random() < 0.3), "c": float(rng.uniform(0.5, 60)) * 1e6}}
def lapack_modes(K, M):
    """Eigenvalues and M-normalised vectors of K phi = lam M phi through the symmetric form M^-1/2 K M^-1/2."""
    d = 1.0 / np.sqrt(M); A = (K * d).T * d; A = 0.5 * (A + A.T)
    lam, V = np.linalg.eigh(A)
    return lam, (V.T * d).T
buildings = [random_building() for _ in range(120)]
w = {"lam": 0, "shape": 0, "top": 0, "capped": 0}; cases = 0; cut = 0
for p in buildings:
    mod = S["build"](p); K, M = mod["K"], mod["M"]; n = len(M); cases += 1
    lam_ref, V = lapack_modes(K, M)
    lams, modes, iters = S["inverse_iteration"](K, M, 3)
    for j in range(min(3, n)):
        e = abs(lams[j] - lam_ref[j]) / lam_ref[j]
        w["lam"] = max(w["lam"], e)
        ph = modes[j]; cosang = abs(ph @ (M * V[:, j])) / math.sqrt((ph @ (M * ph)) * (V[:, j] @ (M * V[:, j])))
        gap = min([abs(lam_ref[j] - lam_ref[i]) / lam_ref[j] for i in range(n) if i != j], default=1.0)
        if gap > 1e-3:                                    # a mode shape is only defined to about (error in lambda / gap)
            w["shape"] = max(w["shape"], 1.0 - min(1.0, cosang))
        w["capped"] = max(w["capped"], iters[j] / 400.0)
    top, _, steps = S["power_iteration"](K, M); cut += steps >= S["POWER_MAXIT"]
    w["top"] = max(w["top"], abs(top - lam_ref[-1]) / lam_ref[-1])
report("Inverse iteration: three lowest eigenvalues, relative error", w["lam"], 1e-7, cases, "random buildings with isolation, dampers, bracing")
report("Inverse iteration: mode shapes, 1 - cos(angle to LAPACK's)", w["shape"], 1e-6, cases)
report("Inverse iteration: steps used / the cap of 400", w["capped"], 0.99, cases, "below 1 means it always stopped by itself")
report("Power iteration: highest eigenvalue, relative error", w["top"], 5e-4, cases, "cut off at its cap of 5000 steps in %d of %d; slow when the top two eigenvalues are close" % (cut, cases))
# two eigenvalues close together: a lightly tuned damper splits the first mode into a tight pair
w = 0; cases = 0
for mu in (0.002, 0.005, 0.02):
    for f in (0.97, 1.0, 1.03):
        p = {"N": 10, "h": 3.2, "m": [3e5] * 10, "k": [4e8] * 10, "system": "frame", "zeta": 0.05, "tmd": {"on": True, "mu": mu, "f": f, "zd": 0.05}}
        mod = S["build"](p); lam_ref, _ = lapack_modes(mod["K"], mod["M"]); lams, _, iters = S["inverse_iteration"](mod["K"], mod["M"], 3); cases += 1
        w = max(w, max(abs(a - b) / b for a, b in zip(lams, lam_ref)))
report("Inverse iteration with two nearly equal eigenvalues (tuned damper)", w, 1e-6, cases)
k0, m0, N0 = 4e8, 3e5, 12
lams, _, _ = S["inverse_iteration"](S["frame_matrix"]([k0] * N0), np.full(N0, m0), 3)
exact = [(2 * math.sqrt(k0 / m0) * math.sin((2 * j + 1) * math.pi / (2 * (2 * N0 + 1)))) ** 2 for j in range(3)]
report("Uniform frame: eigenvalues against the closed-form formula", max(abs(a - b) / b for a, b in zip(lams, exact)), 1e-8, 3)

# =====================================================================================================
section("4. roots of equations")
PROBLEMS = [("x^2 - 2", lambda x: x * x - 2.0, 0.0, 2.0, math.sqrt(2.0)), ("cos x - x", lambda x: math.cos(x) - x, 0.0, 1.0, 0.7390851332151607),
            ("x^3 - 2x - 5", lambda x: x ** 3 - 2 * x - 5.0, 2.0, 3.0, 2.0945514815423265), ("exp(-x) - x", lambda x: math.exp(-x) - x, 0.0, 1.0, 0.5671432904097838),
            ("x^10 - 1 (flat then steep)", lambda x: x ** 10 - 1.0, 0.0, 1.3, 1.0)]
wb = wf = 0
for name, f, a, b, root in PROBLEMS:
    x, it, hist = S["bisection"](f, a, b, 1e-10, 200); wb = max(wb, abs(x - root) / root / 1e-10)
    x, it, hist = S["false_position"](f, a, b, 1e-12, 5000); wf = max(wf, abs(x - root) / root)
report("Bisection: true error / requested tolerance", wb, 1.0, len(PROBLEMS), "its error estimate is a guaranteed bound")
report("False position run to convergence: true relative error", wf, 1e-8, len(PROBLEMS))
x, it, hist = S["fixed_point"](lambda x: math.exp(-x), 0.5, 1e-12, 500)
report("Fixed-point iteration x = exp(-x): true relative error", abs(x - 0.5671432904097838) / 0.5671432904097838, 1e-10, 1)
x, it, hist = S["bisection"](lambda x: x - 1.0, 1.0, 3.0, 1e-12, 200)
report("Bisection when the root sits on an end of the bracket", abs(x - 1.0), 1e-9, 1)
try:
    S["bisection"](lambda x: x * x + 1.0, -1.0, 1.0); raised = False
except ValueError:
    raised = True
flag("Bisection refuses a bracket with no sign change", raised)
tiny = lambda x: 1e-200 * (x - 2.0)                      # values so small that the product of two of them underflows to zero
x, it, hist = S["bisection"](tiny, 0.0, 3.0, 1e-12, 200); x2, _, _ = S["false_position"](tiny, 0.0, 3.0, 1e-12, 200)
report("Root finders on a function whose values are about 1e-200", max(abs(x - 2.0), abs(x2 - 2.0)), 1e-9, 2, "a sign test by multiplication would underflow")

# =====================================================================================================
section("5. statistics, interpolation, regression")
w = {"mean": 0, "std": 0, "interp": 0, "lsq": 0, "fit": 0}; cases = 0
for _ in range(40):
    v = list(rng.normal(3.0, 2.0, size=int(rng.integers(2, 60)))); cases += 1
    w["mean"] = max(w["mean"], abs(S["mean"](v) - np.mean(v)) / abs(np.mean(v)))
    w["std"] = max(w["std"], abs(S["std"](v) - np.std(v, ddof=1)) / np.std(v, ddof=1))
    xs = np.sort(rng.uniform(0, 10, size=int(rng.integers(2, 12)))); ys = rng.normal(size=len(xs))
    for x in list(rng.uniform(-2, 12, size=10)) + [xs[0], xs[-1]]:
        w["interp"] = max(w["interp"], abs(S["interp_linear"](list(xs), list(ys), float(x)) - np.interp(x, xs, ys)))
    X = rng.normal(size=(int(rng.integers(3, 30)), 2)); y = rng.normal(size=len(X))
    a, _ = S["least_squares"](X, y)
    w["lsq"] = max(w["lsq"], relerr(a, np.linalg.lstsq(X, y, rcond=None)[0]))
    h = np.sort(rng.uniform(5, 150, size=int(rng.integers(3, 20)))); T = 0.05 * h ** 0.9 * np.exp(rng.normal(0, 0.08, size=len(h)))
    C, xe, r2, _ = S["fit_power_law"](list(h), list(T)); slope, icept = np.polyfit(np.log(h), np.log(T), 1)
    w["fit"] = max(w["fit"], abs(xe - slope) / abs(slope), abs(C - math.exp(icept)) / math.exp(icept))
report("Mean against numpy", w["mean"], 1e-13, cases)
report("Sample standard deviation against numpy (n - 1)", w["std"], 1e-12, cases)
report("Linear interpolation against numpy.interp, including both ends", w["interp"], 1e-13, cases * 12)
report("Least squares (normal equations + Cholesky) against LAPACK lstsq", w["lsq"], 1e-10, cases)
report("Power-law fit against numpy.polyfit in log-log space", w["fit"], 1e-10, cases)
w = 0
for _ in range(40):
    h = np.sort(rng.uniform(5, 150, size=int(rng.integers(3, 20)))); T = 0.05 * h ** 0.9 * np.exp(rng.normal(0, 0.15, size=len(h)))
    r2 = S["fit_power_law"](list(h), list(T))[2]; lx, ly = np.log(h), np.log(T); fit = np.polyval(np.polyfit(lx, ly, 1), lx)
    w = max(w, abs(r2 - (1 - np.sum((ly - fit) ** 2) / np.sum((ly - ly.mean()) ** 2))))
report("r squared of the power-law fit against its definition", w, 1e-10, 40)

# =====================================================================================================
section("6. Euler's method")
# For M u'' + K u = 0, explicit Euler multiplies mode j by (1 + i w_j h) every step. That gives the exact numbers
# Euler should produce, which checks the time loop itself rather than Euler's (large) error.
w = {"roof": 0, "energy": 0, "order": 0}; cases = 0
for N in (1, 3, 8):
    k = rng.uniform(1e8, 5e8, size=N); m = rng.uniform(1e5, 4e5, size=N); K = S["frame_matrix"](k); lam, V = lapack_modes(K, m); om = np.sqrt(lam)
    u0 = rng.normal(size=N) * 0.01; q0 = V.T @ (m * u0); T1 = 2 * math.pi / om[0]; cases += 1
    for frac in (0.004, 0.001):
        dt = frac * T1; tend = 2 * T1; r = S["euler_free"](K, m, u0, dt, tend); nsteps = int(round(tend / dt)); stride = max(1, nsteps // 400)
        steps = np.arange(0, nsteps + 1, stride)[:len(r["t"])]
        z = (1 + 1j * np.outer(steps, om * dt))            # (1 + i w h), one column per mode
        zn = np.exp(steps[:, None] * np.log(1 + 1j * om[None, :] * dt))
        roof = (zn.real * q0[None, :]) @ V[-1, :]
        w["roof"] = max(w["roof"], float(np.max(np.abs(np.array(r["roof"]) - roof)) / np.max(np.abs(roof))))
        E0 = 0.5 * u0 @ (K @ u0); En = (0.5 * lam[None, :] * q0[None, :] ** 2 * np.abs(zn) ** 2).sum(axis=1) / E0
        w["energy"] = max(w["energy"], float(np.max(np.abs(np.array(r["energy"]) - En) / En)))
k1 = 4.0; exact = math.cos(2.0 * 1.0)                      # one mass: u(1) = cos(w t) with w = 2
errs = [abs(S["euler_free"](np.array([[k1]]), np.array([1.0]), [1.0], h, 1.0)["roof"][-1] - exact) for h in (0.002, 0.001, 0.0005)]
order = math.log(errs[0] / errs[2]) / math.log(4.0)
report("Euler: roof motion against the exact Euler recurrence, mode by mode", w["roof"], 1e-9, cases * 2)
report("Euler: energy against (1 + w^2 h^2)^n summed over the modes", w["energy"], 1e-9, cases * 2)
report("Euler: order of accuracy is 1 (halving the step halves the error)", abs(order - 1.0), 0.02, 3, "measured order %.4f" % order)

# =====================================================================================================
section("7. the building model, assembled a second way")
def reference_model(p, damper=None):
    """Mass, damping and stiffness built independently of the solver's build(): floor by floor in absolute
    (relative-to-ground) coordinates, with LAPACK for the wall and for the first mode.
    damper = (mass, stiffness, damping) to attach; when None they are worked out here from LAPACK's first mode."""
    N = p["N"]; h = p["h"]; m = np.array(p["m"], float); k = np.array(p["k"], float)
    br = p.get("brace") or {}
    if br.get("on"):
        Ld = math.hypot(6.0, h); k = k + 200e9 * br["A"] / Ld * (6.0 / Ld) ** 2      # one diagonal brace: (EA / L) cos^2
    Ks = np.zeros((N, N))
    if p["system"] in ("frame", "dual"):
        for i in range(N):                                  # storey i joins floor i-1 (or the ground) to floor i
            Ks[i, i] += k[i]
            if i > 0:
                Ks[i - 1, i - 1] += k[i]; Ks[i - 1, i] -= k[i]; Ks[i, i - 1] -= k[i]
    if p["system"] in ("wall", "dual"):
        x = h * np.arange(1, N + 1); F = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                a, c = min(x[i], x[j]), max(x[i], x[j]); F[i, j] = a * a * (3 * c - a) / (6 * p["EI"])
        Ks += np.linalg.inv(F)
    w1 = math.sqrt(lapack_modes(Ks, m)[0][0])
    Cs = 2 * p.get("zeta", 0.05) / w1 * Ks
    vc = p.get("visc") or {}
    if vc.get("on"):
        for i in range(N):
            Cs[i, i] += vc["c"]
            if i > 0:
                Cs[i - 1, i - 1] += vc["c"]; Cs[i - 1, i] -= vc["c"]; Cs[i, i - 1] -= vc["c"]
    M, K, C, roof, base = m.copy(), Ks, Cs, N - 1, None
    iso = p.get("iso") or {}
    if iso.get("on"):                                       # one more mass under the building, on a spring to the ground
        n = N + 1; K2 = np.zeros((n, n)); C2 = np.zeros((n, n)); ones = np.ones(N)
        K2[1:, 1:] = Ks; K2[0, 1:] = -(Ks @ ones); K2[1:, 0] = -(Ks @ ones); K2[0, 0] = ones @ Ks @ ones + iso["kb"]
        C2[1:, 1:] = Cs; C2[0, 1:] = -(Cs @ ones); C2[1:, 0] = -(Cs @ ones)
        C2[0, 0] = ones @ Cs @ ones + 2 * iso.get("zb", 0.15) * math.sqrt(iso["kb"] * (iso["mb"] + m.sum()))
        M = np.concatenate([[iso["mb"]], m]); K, C, roof, base = K2, C2, N, 0
    td = p.get("tmd") or {}
    if td.get("on"):
        lam, V = lapack_modes(K, M); phi = V[:, 0] / V[roof, 0]; wref = math.sqrt(lam[0])
        md = td["mu"] * float(np.sum(M * phi ** 2)); wd = td["f"] * wref; kd = md * wd ** 2; cd = 2 * td["zd"] * md * wd
        if damper is not None:
            md, kd, cd = damper
        n = len(M); K2 = np.zeros((n + 1, n + 1)); C2 = np.zeros((n + 1, n + 1)); K2[:n, :n] = K; C2[:n, :n] = C
        for A, v in ((K2, kd), (C2, cd)):
            A[roof, roof] += v; A[n, n] += v; A[roof, n] -= v; A[n, roof] -= v
        K, C, M = K2, C2, np.concatenate([M, [md]])
    return M, C, K, roof, base
w = {"M": 0, "K": 0, "C": 0, "sym": 0, "harm": 0, "md": 0}; cases = 0
for p in buildings:
    mod = S["build"](p); info = mod["tmd_info"]; cases += 1
    M, C, K, roof, base = reference_model(p, (info["md"], info["kd"], info["cd"]) if info else None)
    w["M"] = max(w["M"], relerr(mod["M"], M))
    w["K"] = max(w["K"], float(np.max(np.abs(mod["K"] - K))) / float(np.max(np.abs(K))))
    w["C"] = max(w["C"], float(np.max(np.abs(mod["C"] - C))) / float(np.max(np.abs(C))))
    w["sym"] = max(w["sym"], float(np.max(np.abs(mod["Ks"] - mod["Ks"].T))) / float(np.max(np.abs(mod["Ks"]))))
    if info:                                               # the damper's own mass, against LAPACK's first mode
        M2 = reference_model(p)[0]; w["md"] = max(w["md"], abs(info["md"] - M2[-1]) / M2[-1])
    lam_ref = lapack_modes(mod["K"], mod["M"])[0]; F = -mod["M"] * 0.05 * 9.81
    for Om in list(rng.uniform(0.3, 3.0, size=3) * math.sqrt(lam_ref[0])) + [math.sqrt(lam_ref[0]) * 1.0005]:
        Z = mod["K"] - Om ** 2 * np.diag(mod["M"]) + 1j * Om * mod["C"]; z = np.linalg.solve(Z, F)
        a, b = S["harmonic_solve"](mod["M"], mod["C"], mod["K"], F, Om)
        w["harm"] = max(w["harm"], float(np.max(np.abs((a - 1j * b) - z))) / float(np.max(np.abs(z))) / (np.linalg.cond(Z, np.inf) * EPS))
report("build(): mass vector against the second assembly", w["M"], 1e-12, cases, "base slab and damper included")
report("build(): stiffness matrix against the second assembly", w["K"], 1e-7, cases, "walls differ by (condition number x eps) between two inverses")
report("build(): damping matrix against the second assembly", w["C"], 1e-7, cases)
report("Tuned damper mass (from the solver's own first mode) against LAPACK's", w["md"], 1e-4, cases, "a mode shape is known less precisely than its frequency")
report("Structure stiffness matrix is symmetric: |K - K^T| / |K|", w["sym"], 1e-15, cases, "Cholesky reads only half of it, so it must be exactly symmetric")
report("Damped steady response against a complex-number solve: error / (cond x eps)", w["harm"], 100, cases * 4, "one frequency sits on a resonance")

# the shake test end to end: what analyse() sends to the page, against a complex solve on the second assembly
w = 0; cases = 0
for p in buildings[:40]:
    r = S["analyse"](dict(p, npts=12, cond=False)); mod = S["build"](p); info = mod["tmd_info"]
    M, C, K, roof, base = reference_model(p, (info["md"], info["kd"], info["cd"]) if info else None)
    for i in (0, len(r["freqs"]) // 3, len(r["freqs"]) // 2, len(r["freqs"]) - 1):
        Om = 2 * math.pi * r["freqs"][i]; Z = K - Om ** 2 * np.diag(M) + 1j * Om * C
        z = np.linalg.solve(Z, -M * p["ag"] * 9.81); ref = abs(z[roof] - (z[base] if base is not None else 0.0)); cases += 1
        w = max(w, abs(r["sweep"]["amp"][i] - ref) / ref)
report("Shake test as sent to the page: roof sway against the second assembly", w, 1e-4, cases, "the page gets frequencies rounded to 7 figures, which matters right on a sharp resonance")

# The corners of the slider ranges: the softest isolator under the stiffest core, the lightest damper with no dashpot of its own.
# The rows of these matrices differ in size by a factor of 1e11, and none of them may be mistaken for a singular one.
w = 0; cases = 0; refused = []; clipped = 0
for system in ("wall", "dual", "frame"):
    for N in (2, 40):
        for EI in (1e11, 1e13):
            for kb in (1e5, 4e8):
                for mu in (0.002, 0.15):
                    for f in (0.70, 1.2):
                        for zd in (0.0, 0.4):
                            p = {"N": N, "h": 2.6, "m": [3e5] * N, "k": [4e8] * N, "system": system, "EI": EI, "zeta": 0.005, "ag": 0.05, "npts": 8, "cond": False,
                                 "iso": {"on": True, "kb": kb, "mb": 3e5, "zb": 0.15}, "tmd": {"on": True, "mu": mu, "f": f, "zd": zd}}
                            r = json.loads(S["api"]("analyse", json.dumps(p))); cases += 1
                            if "error" in r:
                                refused.append("%s N=%d kb=%g mu=%g f=%g zd=%g: %s" % (system, N, kb, mu, f, zd, r["error"])); continue
                            clipped += sum(a >= 1e6 for a in r["sweep"]["amp"])
                            mod = S["build"](p); M, C, K = mod["M"], mod["C"], mod["K"]; fr = [r["freqs"][0], r["freqs"][len(r["freqs"]) // 2], r["freqs"][-1]]
                            for fq, a in zip(fr, S["sweep"](mod, fr, 0.05 * 9.81, False, False)["amp"]):
                                Om = 2 * math.pi * fq; Z = K - Om ** 2 * np.diag(M) + 1j * Om * C; z = np.linalg.solve(Z, -M * 0.05 * 9.81)
                                w = max(w, abs(a - abs(z[mod["roof"]] - z[mod["base"]])) / (float(np.max(np.abs(z))) * np.linalg.cond(Z, np.inf) * EPS))
flag("No building at the corners of the slider ranges is refused as singular", not refused,
     "%d of %d refused, %d sweep points capped%s" % (len(refused), cases, clipped, ": " + refused[0] if refused else ""))
report("Shake test at those corners against a complex-number solve: error / (cond x eps)", w, 100, cases * 3)
w = 0; cases = 0
for p in buildings:
    if not p["tmd"]["on"]: continue
    mod = S["build"](p); info = mod["tmd_info"]; M2, C2, K2, roof2, base2 = reference_model(p); cases += 1
    w = max(w, abs(info["kd"] - K2[-1, -1]) / K2[-1, -1], abs(info["cd"] - C2[-1, -1]) / max(C2[-1, -1], 1e-300) if p["tmd"]["zd"] > 0 else 0.0)
report("Tuned damper spring and dashpot against the second assembly", w, 1e-4, cases)
w = 0
for mu in (0.002, 0.03, 0.15):                              # Den Hartog's rule, written out here from the textbook
    f, zd = S["tmd_rule"](mu); w = max(w, abs(f - 1 / (1 + mu)), abs(zd - math.sqrt(3 * mu / (8 * (1 + mu)))))
report("Damper tuning rule against the textbook formulas", w, 1e-15, 3, "f = 1/(1+mu), zeta = sqrt(3 mu / (8 (1 + mu))) on the damper's own frequency")
w = 0
for r_km in (5.0, 10.0, 100.0, 350.0, 900.0):               # Hutton and Boore (1987): -log A0 = 1.110 log10(r/100) + 0.00189 (r - 100) + 3.0
    w = max(w, abs(S["ml_correction"](r_km) - (1.110 * math.log10(r_km / 100.0) + 0.00189 * (r_km - 100.0) + 3.0)))
report("Magnitude distance correction against the published formula", w, 1e-13, 5)

# the wall on its own
EI = 3e12; w = {"int": 0}
for a_, c_ in ((3.0, 3.0), (3.0, 9.0), (12.5, 40.0)):       # unit-load integral: deflection at a from a force at c is the integral of (a - s)(c - s) / EI
    s = np.linspace(0, a_, 200001); y = (a_ - s) * (c_ - s) / EI; integral = float(np.sum((y[1:] + y[:-1]) * 0.5 * (s[1] - s[0])))
    w["int"] = max(w["int"], abs(S["wall_flexibility"]([a_, c_], EI)[0, 1] - integral) / integral)
report("Wall flexibility formula against the unit-load integral", w["int"], 1e-9, 3)
errs = []
for N in (10, 20, 40, 80):                                  # the lumped wall must approach the continuous cantilever as floors are added
    hgt = 96.0 / N; xw = hgt * np.arange(1, N + 1); mw = np.full(N, 1.25e5 * hgt)
    lam = lapack_modes(np.linalg.inv(S["wall_flexibility"](xw, EI)), mw)[0][0]
    errs.append(abs(math.sqrt(lam) - 1.875104068711961 ** 2 * math.sqrt(EI / (1.25e5 * 96.0 ** 4))) / (1.875104068711961 ** 2 * math.sqrt(EI / (1.25e5 * 96.0 ** 4))))
flag("Lumped wall approaches the continuous cantilever frequency as storeys are added",
     all(errs[i + 1] < errs[i] for i in range(3)) and errs[-1] < 0.03, "error %s for 10, 20, 40, 80 storeys" % ", ".join("%.1f%%" % (100 * e) for e in errs))

# stiffness-proportional damping must give the first mode exactly the damping ratio that was asked for
w = 0; cases = 0
for zeta in (0.005, 0.02, 0.05, 0.1):
    p = {"N": 9, "h": 3.2, "m": [3e5] * 9, "k": [4e8 * (1 - 0.04 * i) for i in range(9)], "system": "dual", "EI": 2e12, "zeta": zeta}
    mod = S["build"](p); n = len(mod["M"]); Mi = np.diag(1 / mod["M"]); cases += 1
    A = np.block([[np.zeros((n, n)), np.eye(n)], [-Mi @ mod["K"], -Mi @ mod["C"]]]); s = np.linalg.eigvals(A)
    s = s[np.argmin(np.abs(s))]; w = max(w, abs(-s.real / abs(s) - zeta) / zeta)
report("Damping matrix gives mode 1 the damping ratio asked for", w, 1e-8, cases, "from the eigenvalues of the first-order system")

# the steady response must be what a time integration settles to (a check of the physics, not of the algebra)
p = {"N": 3, "h": 3.2, "m": [3e5, 3e5, 2e5], "k": [4e8, 3e8, 3e8], "system": "frame", "zeta": 0.08, "tmd": {"on": True, "mu": 0.05, "f": 0.95, "zd": 0.12}}
mod = S["build"](p); M, C, K = mod["M"], mod["C"], mod["K"]; n = len(M); F = -M * 0.05 * 9.81; Om = 0.9 * mod["w_ref"]
a, b = S["harmonic_solve"](M, C, K, F, Om); amp = math.hypot(a[mod["roof"]], b[mod["roof"]])
def rhs(t, y):
    return np.concatenate([y[n:], (F * math.cos(Om * t) - C @ y[n:] - K @ y[:n]) / M])
y = np.zeros(2 * n); dt = 2 * math.pi / Om / 400; t = 0.0; peak = 0.0; total = 60 * 400
for i in range(total):                                     # classical 4th-order Runge-Kutta, 60 forcing periods
    k1 = rhs(t, y); k2 = rhs(t + dt / 2, y + dt / 2 * k1); k3 = rhs(t + dt / 2, y + dt / 2 * k2); k4 = rhs(t + dt, y + dt * k3)
    y = y + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4); t += dt
    if i >= total - 400:
        peak = max(peak, abs(y[mod["roof"]]))
report("Steady roof amplitude against a Runge-Kutta time integration (60 periods)", abs(peak - amp) / amp, 2e-4, 1)

# =====================================================================================================
section("8. the code-style static check, calculated a second way")
def reference_static(p, T):
    c = p["code"]; m = np.array(p["m"], float); N = p["N"]; hx = p["h"] * np.arange(1, N + 1); W = m.sum() * 9.81
    Cs = c["SDS"] / (c["R"] / c["I"])
    if T > c["SD1"] / c["SDS"]:
        Cs = c["SD1"] / (T * c["R"] / c["I"])                 # the 1/T branch
    Cs = max(Cs, 0.044 * c["SDS"] * c["I"], 0.01); V = Cs * W
    kexp = 1.0 if T <= 0.5 else 2.0 if T >= 2.5 else 1.0 + (T - 0.5) / 2.0
    F = V * (m * hx ** kexp) / np.sum(m * hx ** kexp)
    Ks = reference_model(dict(p, zeta=0.05, iso=None, tmd=None, visc=None))[2]
    u = np.linalg.solve(Ks, F); drift = c["Cd"] * np.diff(np.concatenate([[0.0], u])) / c["I"]
    return Cs, V, F, u, drift, drift / (c["drift"] * p["h"])
w = {"Cs": 0, "F": 0, "u": 0, "ratio": 0}; cases = 0; branches = set()
for p in buildings:
    p = dict(p, code={"SDS": float(rng.uniform(0.1, 1.5)), "SD1": float(rng.uniform(0.05, 1.0)), "R": float(rng.uniform(1, 8)), "Cd": float(rng.uniform(1, 6.5)), "I": 1.0, "drift": float(rng.uniform(0.005, 0.025))})
    x, m, Ks, k, tri = S["structure"](p); w1, _ = S["first_mode"](Ks, m); T = 2 * math.pi / w1
    st = S["static_check"](p, x, m, Ks, k, tri, T); Cs, V, F, u, drift, ratio = reference_static(p, T); cases += 1
    c_k = np.linalg.cond(Ks, np.inf)
    branches.add("1/T" if T > p["code"]["SD1"] / p["code"]["SDS"] else "flat"); branches.add("floor" if Cs in (0.044 * p["code"]["SDS"], 0.01) else "no floor")
    w["Cs"] = max(w["Cs"], abs(st["Cs"] - Cs) / Cs); w["F"] = max(w["F"], relerr(st["F"], F))
    w["u"] = max(w["u"], relerr(st["u"], u) / (c_k * EPS)); w["ratio"] = max(w["ratio"], relerr(st["ratio"], ratio) / (c_k * EPS))
report("Static check: seismic coefficient Cs", w["Cs"], 1e-12, cases, "branches exercised: " + ", ".join(sorted(branches)))
ww = 0; wres = 0; wcases = 0
for Nw in (10, 20, 30, 40):
    for EIw, hw in ((1e11, 5.0), (3e12, 3.2), (1e13, 2.6)):
        pw = {"N": Nw, "h": hw, "m": [4e5] * Nw, "k": [3e8] * Nw, "system": "wall", "EI": EIw, "code": {"SDS": 0.8, "SD1": 0.4, "R": 5, "Cd": 4.5, "I": 1, "drift": 0.02}}
        xw_, mw_, Kw_, kw_, tw_ = S["structure"](pw); w1w, _ = S["first_mode"](Kw_, mw_); stw = S["static_check"](pw, xw_, mw_, Kw_, kw_, tw_, 2 * math.pi / w1w); wcases += 1
        ww = max(ww, relerr(stw["u"], S["wall_flexibility"](xw_, EIw) @ stw["F"])); wres = max(wres, stw["resid"])
report("Wall up to 40 storeys: sway against flexibility x load (no inverse involved)", ww, 1e-8, wcases)
report("Wall up to 40 storeys: residual of K u = F shown on the page", wres, 1e-7, wcases)
report("Static check: storey forces", w["F"], 1e-12, cases)
report("Static check: sway from K u = F, error / (cond x eps)", w["u"], 200, cases, "Thomas for frames, Cholesky otherwise")
report("Static check: drift / limit, error / (cond x eps)", w["ratio"], 200, cases)
flag("Static check: every branch of the Cs rule was reached", branches == {"1/T", "flat", "floor", "no floor"})

# =====================================================================================================
section("9. design solves")
base = {"N": 8, "h": 3.2, "m": [3e5] * 8, "k": [4e8] * 8, "system": "frame", "zeta": 0.05, "EI": 3e12, "ag": 0.05}
def period_ref(p):
    M, C, K, roof, b = reference_model(dict(p, tmd=None)); return 2 * math.pi / math.sqrt(lapack_modes(K, M)[0][0])
w = {"iso": 0, "cal": 0, "dmg": 0, "stiff": 0}; cases = 0
for p in [b for b in buildings if b["N"] > 1][:40]:
    q = dict(p, iso={"on": False}, tmd={"on": False}); T0 = period_ref(q); cases += 1
    r = S["design_isolation"](q, 2.5 * T0)
    if "error" not in r:
        w["iso"] = max(w["iso"], abs(period_ref(dict(q, iso={"on": True, "kb": r["kb"], "mb": q["m"][0], "zb": 0.15})) - 2.5 * T0) / (2.5 * T0))
    r = S["calibrate"](q, 0.8 * T0)
    if "error" not in r and not q["brace"]["on"]:
        w["cal"] = max(w["cal"], abs(r["scale"] - 1 / 0.64) / (1 / 0.64))       # period goes as 1 / sqrt(stiffness)
    r = S["damage"](q, 1.3 * T0)
    if "error" not in r and r["exact"] is not None:
        w["dmg"] = max(w["dmg"], abs(r["alpha"] - 1 / 1.69) / (1 / 1.69))
    r = S["design_stiffness"](dict(q, code={"SDS": 0.8, "SD1": 0.4, "R": 5, "Cd": 4.5, "I": 1, "drift": 0.02}))
    if "error" not in r:
        s = r["bisection"]["s"]; w["stiff"] = max(w["stiff"], abs(S["drift_ratio_for_scale"](dict(q, code={"SDS": 0.8, "SD1": 0.4, "R": 5, "Cd": 4.5, "I": 1, "drift": 0.02}), s) - 1.0),
                                                   abs(r["false_position"]["s"] - s) / s, abs(r["fixed_point"]["s"] - s) / s)
report("Isolator design: period reached against the second model", w["iso"], 1e-6, cases)
report("Calibration: stiffness factor against 1 / (period ratio)^2", w["cal"], 1e-6, cases)
report("Damage check: stiffness kept against 1 / (period ratio)^2", w["dmg"], 1e-6, cases)
report("Stiffness design: drift / limit = 1 at the answer, and the three root finders agree", w["stiff"], 1e-4, cases)
# the damper: a main mass (m = k = 1) with an attached mass mu, spring mu f^2, dashpot 2 zd mu f, forced on the main mass.
# Solving the two equations by hand gives the main mass's amplitude in closed form:
def two_mass(mu, f, zd, Om):
    kd = mu * f * f; g = kd + 1j * 2 * zd * mu * f * Om
    return np.abs((g - mu * Om ** 2) / ((1 + g - Om ** 2) * (g - mu * Om ** 2) - g * g))
w = 0; cases = 0
for _ in range(30):
    mu = float(rng.uniform(0.005, 0.15)); f = float(rng.uniform(0.8, 1.1)); zd = float(rng.uniform(0.01, 0.3)); cases += 1
    Om = 0.6 + 0.8 * np.arange(401) / 400; ref = two_mass(mu, f, zd, Om); left, right = S["den_hartog_case"](mu, f, zd, 401)
    w = max(w, abs(left - ref[Om < f].max()) / ref[Om < f].max(), abs(right - ref[Om >= f].max()) / ref[Om >= f].max())
report("Two-mass damper response against the closed-form solution", w, 1e-9, cases)
w = 0; wpk = 0; cases = 0; where = ""
for mu in (0.01, 0.05, 0.15):
    Om = np.linspace(0.6, 1.4, 4001)[None, None, :]; f_rule, z_rule = S["tmd_rule"](mu)
    fs_ = np.linspace(f_rule - 0.03, f_rule + 0.03, 61)[:, None, None]; zs_ = np.linspace(0.6 * z_rule, 1.5 * z_rule, 91)[None, :, None]
    peaks = two_mass(mu, fs_, zs_, Om).max(axis=2); i, j = np.unravel_index(np.argmin(peaks), peaks.shape); cases += peaks.size
    pk_rule = float(two_mass(mu, f_rule, z_rule, Om[0, 0]).max())
    if (pk_rule - peaks[i, j]) / peaks[i, j] > w:
        w = (pk_rule - peaks[i, j]) / peaks[i, j]; where = "mu %.2f: rule f %.4f zd %.4f, best f %.4f zd %.4f" % (mu, f_rule, z_rule, fs_[i, 0, 0], zs_[0, j, 0])
    wpk = max(wpk, abs(pk_rule - math.sqrt(1 + 2 / mu)) / math.sqrt(1 + 2 / mu))
report("Damper rule: how much higher its peak is than the best damper found by brute force", w, 0.005, cases, where or "the rule's own point was the best on the grid")
report("Damper rule: peak against the textbook sqrt(1 + 2/mu)", wpk, 0.03, 3)
w = 0; cases = 0
for zeta in (0.02, 0.05):
    for target in (0.3, 0.5):
        p = dict(base, zeta=zeta); r = S["design_tmd"](p, target, 0.05 * 9.81); cases += 1
        if "error" in r or r["smallest"]: continue
        m0 = S["build"](dict(p, tmd={"on": False})); f1 = m0["w_ref"] / (2 * math.pi)
        dense = lambda mod: max(S["roof_amp"](mod, *S["harmonic_solve"](mod["M"], mod["C"], mod["K"], -mod["M"], 2 * math.pi * f1 * (0.6 + 0.85 * i / 4000))) for i in range(4001))
        left = dense(S["build"](S["with_tmd"](p, r["mu"]))) / dense(m0)
        w = max(w, abs(left - (1 - target)))
report("Damper design: sway left, re-measured with a 4001-point scan, against the target", w, 0.01, cases)

# =====================================================================================================
section("10. earthquake detection")
x = list(rng.normal(size=900)); fs = 20.0; r = S["sta_lta"](x, fs, 1.0, 15.0); ns, nl = 20, 300; xa = np.array(x) ** 2; w = 0
for i in range(ns + nl - 1, 900):
    w = max(w, abs(r[i] - np.mean(xa[i + 1 - ns:i + 1]) / np.mean(xa[i + 1 - ns - nl:i + 1 - ns])) / r[i])
report("STA/LTA against a direct window-by-window calculation", w, 1e-9, 900 - ns - nl + 1)
wp = ws = wd = 0; cases = 0; missed = 0; early = 0.0
for dist in (70, 120, 250, 400, 650, 900):
    for mag in (5.0, 6.0, 7.0):
        for seed in range(1, 6):
            rec = S["synth_seismogram"](float(dist), mag, noise=0.02, seed=seed); pk = S["pick_arrivals"](rec["x"], rec["fs"], 5.0); cases += 1
            if pk["tP"] is None or pk["tS"] is None:
                missed += 1; continue
            wp = max(wp, abs(pk["tP"] - rec["tP"])); ws = max(ws, abs(pk["tS"] - rec["tS"])); early = max(early, rec["tP"] - pk["tP"], rec["tS"] - pk["tS"])
            wd = max(wd, abs((pk["tS"] - pk["tP"]) * 6.0 * 3.5 / 2.5 - dist))
report("P pick: worst error in seconds (magnitude 5 to 7, 70 to 900 km, noise 0.02)", wp, 1.0, cases, "always late: the 1 s averaging window has to fill")
report("S pick: worst error in seconds", ws, 1.0, cases)
report("Picks are never early: largest (true - picked) in seconds", early, 0.0, cases)
report("Distance from the S-P gap: worst error in km", wd, 5.0, cases, "%d of %d recordings had no pick" % (missed, cases))
flag("Every recording in that range gives both picks", missed == 0)
wnear = 0; used = 0; nodist = 0; nearest_given = 999; farthest_none = 0; short = 0     # a station so close that the S wave follows the P wave within 7 s
for dist in range(30, 72):
    for mag in (5.0, 6.0, 7.0):
        for seed in (1, 2, 3):
            rec = S["synth_seismogram"](float(dist), mag, noise=0.02, seed=seed); pk = S["pick_arrivals"](rec["x"], rec["fs"], 5.0)
            if pk["tS"] is None:
                nodist += 1; farthest_none = max(farthest_none, dist)
            else:
                e = (pk["tS"] - pk["tP"]) * 6.0 * 3.5 / 2.5 - dist
                used += 1; nearest_given = min(nearest_given, dist); wnear = max(wnear, abs(e)); short += e < 0
report("Stations 30 to 71 km away: distance error in km when a distance is given at all", wnear, 6.5, used + nodist,
       "%d of %d gave no distance; nothing nearer than %d km gave one and nothing beyond %d km failed to; %d of the %d distances given read short"
       % (nodist, used + nodist, nearest_given, farthest_none, short, used))
early = {}                                                  # 90 s of quiet before the P wave: does the trigger fire on the noise?
for noise in (0.02, 0.2):
    for thr in (2.0, 3.0, 4.0, 5.0):
        early[noise, thr] = 0
        for seed in range(1, 31):
            rec = S["synth_seismogram"](300.0, 6.0, noise=noise, seed=seed); pk = S["pick_arrivals"](rec["x"], rec["fs"], thr)
            early[noise, thr] += pk["tP"] is not None and pk["tP"] < rec["tP"] - 1.0
flag("No trigger on noise at threshold 4 or 5 in 90 s of quiet (30 recordings)", early[0.02, 4.0] == 0 and early[0.02, 5.0] == 0,
     "early triggers out of 30: %d at threshold 2, %d at threshold 3, %d at 4, %d at 5" % tuple(early[0.02, t] for t in (2.0, 3.0, 4.0, 5.0)))
flag("Ten times the noise gives the same early triggers (the trigger is a ratio)", all(early[0.2, t] == early[0.02, t] for t in (2.0, 3.0, 4.0, 5.0)))
quiet = sum(S["pick_arrivals"]([float(v) for v in rng.normal(0, 0.02, size=4000)], 20.0, 5.0)["tP"] is not None for _ in range(40))
flag("Pure noise does not trigger at threshold 5", quiet == 0, "%d false triggers in 40 noise-only recordings" % quiet)
w = 0; cases = 0
for _ in range(200):                                       # exact distances must give the exact point
    pts = [tuple(rng.uniform(-400, 400, size=2)) for _ in range(int(rng.integers(3, 7)))]; tr = rng.uniform(-300, 300, size=2)
    x0, y0, cond, res = S["locate"](pts, [math.hypot(tr[0] - a, tr[1] - b) for a, b in pts]); cases += 1
    w = max(w, math.hypot(x0 - tr[0], y0 - tr[1]) / (cond * EPS * 800))
report("Epicentre from exact distances: error / (cond x eps x 800 km)", w, 50, cases)
w = 0
for lat, lon in ((22.0, 47.0), (31.0, 60.0), (26.0, 54.0), (28.4, 51.7)):
    xk, yk = S["to_xy"](lat, lon, 26.0, 54.0); la, lo = S["to_latlon"](xk, yk, 26.0, 54.0); w = max(w, abs(la - lat), abs(lo - lon))
report("Map conversion there and back, in degrees", w, 1e-12, 4)
def great_circle(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0]); dl = math.radians(b[1] - a[1])
    return 6371.0 * 2 * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
PLACES = {"UOSS": (24.9453, 56.2042), "Abu Dhabi": (24.45, 54.38), "Dubai": (25.20, 55.27), "Doha": (25.29, 51.53), "Muscat": (23.59, 58.41),
          "Manama": (26.23, 50.59), "Bandar Abbas": (27.19, 56.27), "Shiraz": (29.59, 52.58)}
w = 0; cases = 0; worst_pair = ""
for qlat in np.linspace(22, 31, 10):
    for qlon in np.linspace(47, 60, 14):
        for name, pl in PLACES.items():
            gc = great_circle((qlat, qlon), pl)
            if gc < 50: continue
            a = S["to_xy"](qlat, qlon, 26.0, 54.0); b = S["to_xy"](pl[0], pl[1], 26.0, 54.0); flat = math.hypot(a[0] - b[0], a[1] - b[1]); cases += 1
            if abs(flat - gc) / gc > w: w = abs(flat - gc) / gc; worst_pair = "%.0fN %.0fE to %s" % (qlat, qlon, name)
report("Flat-map distance against the great-circle distance, anywhere on the map", w, 0.06, cases, "worst: " + worst_pair + "; a known limit of a flat map")
st = [{"name": n, "lat": PLACES[n][0], "lon": PLACES[n][1]} for n in ("UOSS", "Abu Dhabi", "Doha", "Muscat", "Manama")]
werr = wml = wwarn = 0; cases = 0; nofix = 0
for qlat, qlon in ((27.7, 55.2), (26.6, 54.9), (28.9, 51.5), (25.6, 57.9), (29.5, 56.5), (23.2, 55.0)):
    for mag in (5.5, 6.5, 7.2):
        d = S["detect"]({"lat": qlat, "lon": qlon, "mag": mag, "noise": 0.02, "thr": 5.0, "delay": 5.0, "stations": st, "cities": st, "show": 0}); cases += 1
        if d["epi"] is None:
            nofix += 1; continue
        werr = max(werr, d["epi"]["err_km"]); wml = max(wml, abs(d["epi"]["ml_mean"] - mag))
        ex, ey = S["to_xy"](qlat, qlon, 26.0, 54.0)
        for c in d["cities"]:                              # warning = S arrival at the city - (first P pick + processing delay)
            cx, cy = S["to_xy"](PLACES[c["name"]][0], PLACES[c["name"]][1], 26.0, 54.0)
            wwarn = max(wwarn, abs(c["warn"] - (math.hypot(cx - ex, cy - ey) / 3.5 - (d["first_alarm"] + 5.0))))
report("Whole pipeline: epicentre error in km (five stations, magnitude 5.5 to 7.2)", werr, 15.0, cases, "%d of %d had too few picks to locate" % (nofix, cases))
report("Whole pipeline: magnitude recovered, error in magnitude units", wml, 0.1, cases)
report("Warning time against the definition, in seconds", wwarn, 1e-9, cases)
t = np.sort(rng.uniform(0, 30, size=400)); xv = np.sin(t); out = S["resample_uniform"](list(t), list(xv), 20.0); grid = t[0] + np.arange(len(out)) / 20.0
report("Resampling against numpy.interp", float(np.max(np.abs(np.array(out) - np.interp(grid, t, xv)))), 1e-12, len(out))

# =====================================================================================================
section("11. numbers on their way to the page")
payload = json.loads(S["api"]("analyse", json.dumps(dict(base, npts=60, cond=True))))
direct = S["analyse"](dict(base, npts=60, cond=True))
w = max(abs(a["T"] - b["T"]) / b["T"] for a, b in zip(payload["modes"], direct["modes"]))
w = max(w, relerr(payload["static"]["u"], direct["static"]["u"]), relerr(payload["sweep"]["amp"], direct["sweep"]["amp"]))
report("Rounding to 7 significant figures for the page: largest change", w, 5e-7, 3)

print("\n%d checks, %d failed" % (len(rows), fails))
if "--json" in sys.argv:
    (ROOT / "accuracy.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
sys.exit(1 if fails else 0)
