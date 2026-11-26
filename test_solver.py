"""Tests the Python solver exactly as it ships inside index.html.
Run:  python test_solver.py      (needs numpy; numpy.linalg is used here only as a referee)"""
import re, sys, math, json
import numpy as np

html = open("index.html", encoding="utf-8").read()
src = re.search(r'<script type="text/python" id="solver">\n(.*?)</script>', html, re.S).group(1)
assert "linalg" not in src.replace("no numpy.linalg routine", ""), "solver must not call numpy.linalg"
ns = {}
exec(compile(src, "solver(index.html)", "exec"), ns)

fails = 0
def report(ok, name, detail=""):
    global fails
    fails += (not ok)
    print(("PASS  " if ok else "FAIL  ") + name + ("   " + detail if detail else ""))

# 1. the built-in verification suite (the same one the page runs)
for r in ns["verify"]():
    report(r["ok"], r["name"], "got %.8g, expected %.8g, error %.1e (allowed %.0e)" % (r["got"], r["expected"], r["err"], r["tol"]))

# 2. referee checks against numpy.linalg
rng = np.random.default_rng(0)
A = rng.normal(size=(12, 12)); b = rng.normal(size=12); S = A @ A.T + 12 * np.eye(12)
report(np.allclose(ns["gauss_solve"](A, b), np.linalg.solve(A, b)), "referee: Gauss elimination vs numpy")
report(np.allclose(ns["lu_solve"](ns["lu_decompose"](A), b), np.linalg.solve(A, b)), "referee: LU vs numpy")
report(np.isclose(ns["lu_det"](ns["lu_decompose"](A)), np.linalg.det(A)), "referee: determinant vs numpy")
report(np.allclose(ns["gauss_jordan_inverse"](A), np.linalg.inv(A)), "referee: inverse vs numpy")
report(np.allclose(ns["cholesky"](S), np.linalg.cholesky(S)), "referee: Cholesky vs numpy")
report(np.isclose(ns["cond_inf"](A), np.linalg.cond(A, np.inf)), "referee: condition number vs numpy")
p = {"N": 12, "h": 3.2, "m": [3e5 * (1 + 0.1 * (i % 3)) for i in range(12)], "k": [4e8 * (1 - 0.03 * i) for i in range(12)],
     "system": "dual", "EI": 3e12, "zeta": 0.05, "iso": {"on": True, "kb": 3e7, "mb": 3e5},
     "tmd": {"on": True, "mu": 0.03, "f": 0.97, "zd": 0.1}}
mod = ns["build"](p)
w = np.sqrt(np.sort(np.linalg.eigvals(np.diag(1 / mod["M"]) @ mod["K"]).real))[:3]
mine = [2 * math.pi / m["T"] for m in ns["system_modes"](mod, 3)]
report(np.allclose(mine, w, rtol=1e-6), "referee: 3 lowest frequencies of an isolated dual building with damper", str(np.round(mine, 5)))
Om = 2.0; n = len(mod["M"]); F = -mod["M"] * 0.5
z = np.linalg.solve(mod["K"] - Om ** 2 * np.diag(mod["M"]) + 1j * Om * mod["C"], F)   # complex-number solution
a, bb = ns["harmonic_solve"](mod["M"], mod["C"], mod["K"], F, Om)
report(np.allclose(a, z.real) and np.allclose(bb, -z.imag), "referee: damped response vs complex-number solve")

# 3. the tuning rule for the damper's own damping, checked by brute force
mu = 0.05; f_rule, z_rule = ns["tmd_rule"](mu); best = (9e9, None)
for zd in np.linspace(0.06, 0.22, 33):
    pk = max(ns["den_hartog_case"](mu, f_rule, float(zd), 401))
    if pk < best[0]: best = (pk, float(zd))
report(abs(best[1] - z_rule) / z_rule < 0.12, "damper damping rule vs brute-force search", "best %.3f, rule %.3f" % (best[1], z_rule))

# 4. every page call returns valid JSON without an error
base = {"N": 8, "h": 3.2, "m": [3e5] * 8, "k": [4e8] * 8, "system": "frame", "zeta": 0.05, "EI": 3e12, "ag": 0.05}
st = [{"name": "A", "lat": 24.9, "lon": 56.2}, {"name": "B", "lat": 24.45, "lon": 54.38}, {"name": "C", "lat": 25.29, "lon": 51.53}, {"name": "D", "lat": 23.59, "lon": 58.41}]
calls = [("analyse", base), ("design_stiffness", base), ("design_tmd", {"p": base, "target": 0.4}), ("design_isolation", {"p": base, "T": 2.5}),
         ("calibrate", {"p": base, "T": 1.2}), ("damage", {"p": base, "T": 1.1}), ("regression", {"h": [10, 20, 30, 40, 50, 60], "T": [0.4, 0.7, 1.0, 1.3, 1.6, 1.8]}),
         ("euler", base), ("race", base), ("det", base), ("verify", {}),
         ("detect", {"lat": 27.7, "lon": 55.2, "mag": 6, "stations": st, "cities": st, "show": 0}),
         ("record", {"x": ns["synth_seismogram"](200, 6)["x"], "fs": 20}), ("seismometer", {"f0": 1, "zeta": 0.7, "freqs": [0.5, 1, 2]})]
for name, arg in calls:
    r = json.loads(ns["api"](name, json.dumps(arg)))
    report(not (isinstance(r, dict) and "error" in r), "page call: " + name, r.get("error", "") if isinstance(r, dict) else "")
d = json.loads(ns["api"]("detect", json.dumps({"lat": 27.7, "lon": 55.2, "mag": 6, "stations": st, "cities": st, "show": 0})))
report(d["epi"] is not None and d["epi"]["err_km"] < 10, "detection pipeline finds the planted epicentre", "error %.2f km" % d["epi"]["err_km"])

print("\n%d failed" % fails)
sys.exit(1 if fails else 0)
