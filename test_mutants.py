"""Do the built-in checks notice when the solver is wrong?
Run:  python test_mutants.py      (needs numpy; about two minutes)

Each entry below is one deliberate mistake: a piece of the solver's source and what to replace it with.
The script makes each wrong copy in memory, runs the solver's own verify() on it (the checks behind the
Verify tab of the page) and expects at least one check to fail. A wrong copy that passes every check is a
hole in the checks. index.html itself is never changed.

If an entry's text is no longer found in the solver, the solver was edited there: update the entry.
"""
import re, sys, warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent
html = (ROOT / "index.html").read_text(encoding="utf-8")
src = re.search(r'<script type="text/python" id="solver">\n(.*?)</script>', html, re.S).group(1)

# (what is wrong, text in the solver, replacement)
MUTANTS = [
    ('tmd damping rule: (1+mu) -> (1+mu)^3 under the root',
     'math.sqrt(3.0 * mu / (8.0 * (1.0 + mu)))',
     'math.sqrt(3.0 * mu / (8.0 * (1.0 + mu) ** 3))'),
    ('tmd damping rule: 3mu/8 -> mu/8 (42 % too small)',
     'math.sqrt(3.0 * mu / (8.0 * (1.0 + mu)))',
     'math.sqrt(1.0 * mu / (8.0 * (1.0 + mu)))'),
    ('tmd tuning rule: 1/(1+mu) -> 1 - mu',
     'return 1.0 / (1.0 + mu), ',
     'return 1.0 - mu, '),
    ('tmd tuning rule: 1/(1+mu) -> 1/sqrt(1+mu)',
     'return 1.0 / (1.0 + mu), ',
     'return 1.0 / math.sqrt(1.0 + mu), '),
    ('ELF: lower limit 0.044 SDS I removed',
     'Cs = max(Cs, 0.044 * SDS * I, 0.01)',
     'Cs = max(Cs, 0.01)'),
    ('ELF: Cs = SD1/(T R/I) -> SD1/(T^2 R/I)',
     'Cs = SD1 / (T1 * R / I)',
     'Cs = SD1 / (T1 * T1 * R / I)'),
    ('ELF: plateau Cs = SDS/(R/I) -> SDS',
     'Cs = SDS / (R / I)',
     'Cs = SDS'),
    ('ELF: height exponent fixed at 1',
     'kexp = interp_linear([0.5, 2.5], [1.0, 2.0], T1)',
     'kexp = 1.0'),
    ('ELF: storey forces not weighted by height at all',
     'wgt = m * G * x ** kexp',
     'wgt = m * G * x ** 0'),
    ('ELF: Cd/I amplification dropped from the drift',
     'drift = Cd * d_el / I',
     'drift = d_el'),
    ('ELF: weight W = sum(m) without g',
     'W = float(m.sum()) * G; V = Cs * W',
     'W = float(m.sum()); V = Cs * W'),
    ('ELF: soft storey threshold 0.7 -> 0.5',
     'k[i] < 0.7 * k[i + 1]',
     'k[i] < 0.5 * k[i + 1]'),
    ('brace: cos^2 -> cos',
     '/ Ld * (w / Ld) ** 2',
     '/ Ld * (w / Ld)'),
    ('isolation: wrong sign in the slab coupling (T = [+1 | I])',
     'T = np.hstack([-np.ones((N, 1)), np.eye(N)])',
     'T = np.hstack([np.ones((N, 1)), np.eye(N)])'),
    ('isolation: isolator stiffness counted twice',
     'K[0, 0] += kb',
     'K[0, 0] += 2.0 * kb'),
    ('isolation: isolator damping uses slab mass only',
     'math.sqrt(kb * (mb + float(m.sum())))',
     'math.sqrt(kb * mb)'),
    ('tmd: modal mass -> total mass',
     'modal_mass = float(np.sum(M * phi_ref ** 2))',
     'modal_mass = float(np.sum(M))'),
    ('tmd: damper attached to the first floor instead of the roof',
     'A[roof, roof] += val; A[n, n] += val; A[roof, n] -= val; A[n, roof] -= val',
     'A[0, 0] += val; A[n, n] += val; A[0, n] -= val; A[n, 0] -= val'),
    ('tmd: damper damping cd doubled',
     'cd = 2.0 * float(tmd.get("zd", 0.1)) * md * wd',
     'cd = 4.0 * float(tmd.get("zd", 0.1)) * md * wd'),
    ('floor dampers: identity instead of the storey chain',
     'Cs = Cs + frame_matrix(np.full(N, float(v.get("c", 0.0))))',
     'Cs = Cs + np.eye(N) * float(v.get("c", 0.0))'),
    ('damping matrix: zeta halved',
     'Cs = (2.0 * zeta / w1) * Ks',
     'Cs = (1.0 * zeta / w1) * Ks'),
    ('harmonic: sign of both C blocks flipped (b changes sign)',
     'S = np.block([[D, Om * C], [-Om * C, D]])',
     'S = np.block([[D, -Om * C], [Om * C, D]])'),
    ('sweep: load uses a unit vector instead of the masses',
     'M = mod["M"]; n = len(M); F = -M * ag',
     'M = mod["M"]; n = len(M); F = -np.ones(n) * ag * float(np.mean(M))'),
    ('roof_amp: base slab not subtracted',
     'ar = a[r] - (a[q] if q is not None else 0.0); br = b[r] - (b[q] if q is not None else 0.0)',
     'ar = a[r]; br = b[r]'),
    ('S-P distance: vp vs/(vp - vs) -> vp vs/(vp + vs)',
     '* vp * vs / (vp - vs)',
     '* vp * vs / (vp + vs)'),
    ('magnitude correction: 0.00189 -> 0.0189',
     '0.00189 * (r - 100.0)',
     '0.0189 * (r - 100.0)'),
    ('magnitude: log10 -> natural log',
     'math.log10(peak) + ml_correction',
     'math.log(peak) + ml_correction'),
    ('flat map: cos(latitude) dropped',
     '111.32 * math.cos(math.radians(lat0))',
     '111.32'),
    ('warning time: S speed -> P speed',
     'dc / vs - (first_alarm + delay)',
     'dc / vp - (first_alarm + delay)'),
    ('STA/LTA: long window overlaps the short one',
     'l = (cs[i + 1 - ns] - cs[i + 1 - ns - nl]) / nl',
     'l = (cs[i + 1] - cs[i + 1 - nl]) / nl'),
    ('P pick reported 1.0 s late',
     'out["tP"] = iP / fs',
     'out["tP"] = iP / fs + 1.0'),
    ('S pick reported 2.0 s late',
     'out["tS"] = iS / fs',
     'out["tS"] = iS / fs + 2.0'),
    ('resampling: never moves past the first segment',
     'while j < len(t) - 2 and t[j + 1] < tt:',
     'while False and t[j + 1] < tt:'),
    ('condition number: ||A|| factor dropped',
     'return norm_inf(A) * norm_inf(gauss_jordan_inverse(A))',
     'return norm_inf(gauss_jordan_inverse(A))'),
    ('norm: column sums instead of row sums',
     'np.sum(np.abs(np.array(A, float)), axis=1)',
     'np.sum(np.abs(np.array(A, float)), axis=0)'),
    ('regression: r^2 = SSres/SStot',
     'r2 = 1.0 - sr / st if st > 0 else 1.0',
     'r2 = sr / st if st > 0 else 1.0'),
    ('wall flexibility 10 % too stiff everywhere',
     'F[i, j] = a * a * (3.0 * c - a) / (6.0 * EI)',
     'F[i, j] = a * a * (3.0 * c - a) / (6.6 * EI)'),
    ('wall: off-diagonal uses (3c - a) -> (3c - 0.8a) only when i != j and a > one storey',
     'F[i, j] = a * a * (3.0 * c - a) / (6.0 * EI)',
     'F[i, j] = a * a * (3.0 * c - (a if (i == j or min(i, j) == 0) else 0.8 * a)) / (6.0 * EI)'),
    ('interp_linear: wrong weight in inner segments (t squared) for tables with more than 2 points',
     't = (x - xs[i]) / (xs[i + 1] - xs[i])',
     't = (x - xs[i]) / (xs[i + 1] - xs[i]); t = t * t if len(xs) > 2 else t'),
    ('LU: no pivoting',
     'p = k + int(np.argmax(np.abs(A[k:, k])))\n        if A[p, k] == 0.0:\n            continue',
     'p = k\n        if A[p, k] == 0.0:\n            continue'),
    ('Gauss-Jordan: no pivoting',
     'p = k + int(np.argmax(np.abs(W[k:, k])))',
     'p = k'),
    ('inverse iteration: deflation after the solve removed',
     '            for ph in modes:\n                y = y - (ph @ (m * y)) * ph\n',
     ''),
    ('std: divide by n instead of n - 1',
     '/ (len(v) - 1))',
     '/ len(v))'),
    ('least squares in locate(): right-hand side sign of d terms',
     'b.append(d[0] ** 2 - di ** 2 +',
     'b.append(di ** 2 - d[0] ** 2 +'),
    ('wall stiffness: symmetrising removed',
     'Ks += 0.5 * (Kw + Kw.T)',
     'Ks += Kw'),
    ('root finders: sign test back to a product',
     'return (u > 0.0 and v > 0.0) or (u < 0.0 and v < 0.0)',
     'return u * v > 0'),
    ("S pick: the 'too close' refusal removed",
     '    if start < len(r2) and r2[start] > thr:\n        out["too_close"] = True\n        return out\n',
     ''),
    ('Jacobi: divergence guard removed',
     'if ea < es or not math.isfinite(ea) or size > blown:\n            break\n    return x, it, hist\n\n\ndef sor',
     'if ea < es or not math.isfinite(ea):\n            break\n    return x, it, hist\n\n\ndef sor'),
    ('Cholesky solve: forward substitution skips the division',
     'y[i] = (b[i] - L[i, :i] @ y[:i]) / L[i, i]',
     'y[i] = (b[i] - L[i, :i] @ y[:i])'),
    ('Thomas: wrong sign in the back substitution',
     'x[k] = (r[k] - g[k] * x[k + 1]) / f[k]',
     'x[k] = (r[k] + g[k] * x[k + 1]) / f[k]'),
    ('SOR: relaxation term dropped',
     'xi = omega * (b[i] - s) / A[i, i] + (1.0 - omega) * x[i]',
     'xi = omega * (b[i] - s) / A[i, i]'),
    ('Euler: velocity updated with the new position (not Euler any more)',
     'u, v = u + dt * v, v + dt * a',
     'u = u + dt * v; v = v - dt * (Ks @ u) / m'),
    ('false position: formula uses the midpoint',
     'c = b - fb * (a - b) / (fa - fb); fc = f(c)',
     'c = 0.5 * (a + b); fc = f(c)'),
    ('detect: distance uses the P pick twice',
     'dest = (pk["tS"] - pk["tP"]) * vp * vs / (vp - vs)',
     'dest = (pk["tS"] - pk["tP"]) * vp * vp / (vp - vs)'),
    ('static check: design drift uses storey 1 height twice (limit x 2)',
     'ratio = drift / (limit * h)',
     'ratio = drift / (limit * h * 2.0)'),
    ('peak search: refinement removed',
     '    for _ in range(refine):',
     '    for _ in range(0):'),
]

# Wrong copies that no check can tell from the real solver, with the reason. Keep this list short.
SAME_RESULTS = {
    "inverse iteration: deflation after the solve removed":
        "the modes already found are removed before every solve as well, so the second removal only guards against rounding",
}

caught = 0; holes = []; stale = []
for name, old, new in MUTANTS:
    if src.count(old) == 0:
        stale.append(name); print("STALE   %s" % name); continue
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            ns = {}
            exec(compile(src.replace(old, new), "wrong copy", "exec"), ns)
            failed = [r["name"] for r in ns["verify"]() if not r["ok"]]
        why = ("%d check(s), first: %s" % (len(failed), failed[0])) if failed else None
    except Exception as ex:                      # a wrong copy that crashes has been noticed too
        why = "verify() stopped with %s" % type(ex).__name__
    if why:
        caught += 1; print("CAUGHT  %-78s %s" % (name[:78], why[:90]))
    elif name in SAME_RESULTS:
        print("SAME    %-78s %s" % (name[:78], SAME_RESULTS[name]))
    else:
        holes.append(name); print("MISSED  %s" % name)

print("\n%d wrong copies: %d caught, %d with the same results as the real solver, %d missed, %d stale"
      % (len(MUTANTS), caught, len(MUTANTS) - caught - len(holes) - len(stale), len(holes), len(stale)))
sys.exit(1 if holes or stale else 0)
