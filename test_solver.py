"""Tests the Python solver exactly as it ships inside index.html, plus a few checks of the page itself.
Run:  python test_solver.py      (needs numpy; numpy.linalg is used here only as a referee)

Sections
  1  the built-in verification suite (the same one tab 5 of the page runs)
  2  referee checks against numpy.linalg
  3  the damper tuning rule, checked by brute force
  4  every page call returns valid JSON without an error
  5  bugs that were fixed stay fixed
  6  the corners of the slider ranges
  7  the page and its script agree with each other and with the README
"""
import re, sys, math, json, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
html = (ROOT / "index.html").read_text(encoding="utf-8")
src = re.search(r'<script type="text/python" id="solver">\n(.*?)</script>', html, re.S).group(1)
assert "linalg" not in src.replace("no numpy.linalg routine", ""), "solver must not call numpy.linalg"
warnings.simplefilter("error", RuntimeWarning)       # an overflow or a division by zero inside the solver fails the run
ns = {}
exec(compile(src, "solver(index.html)", "exec"), ns)

fails = 0
def report(ok, name, detail=""):
    global fails
    fails += (not ok)
    print(("PASS  " if ok else "FAIL  ") + name + ("   " + detail if detail else ""))

def call(name, arg):
    """One call through the same JSON door the page uses."""
    return json.loads(ns["api"](name, json.dumps(arg)))

def crashed(r):
    """True when a reply is an uncaught Python exception rather than an answer or a plain-language message."""
    return isinstance(r, dict) and bool(re.match(r"[A-Z]\w*(Error|Exception|Warning): ", str(r.get("error", ""))))

# ---------------------------------------------------------------- 1. the built-in verification suite
checks = ns["verify"]()
for r in checks:
    report(r["ok"], r["name"], "got %.8g, expected %.8g, error %.1e (allowed %.0e)" % (r["got"], r["expected"], r["err"], r["tol"]))

# ---------------------------------------------------------------- 2. referee checks against numpy.linalg
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

# ---------------------------------------------------------------- 3. the damper tuning rule, by brute force
mu = 0.05; f_rule, z_rule = ns["tmd_rule"](mu); best = (9e9, None)
for zd in np.linspace(0.06, 0.22, 33):
    pk = max(ns["den_hartog_case"](mu, f_rule, float(zd), 401))
    if pk < best[0]: best = (pk, float(zd))
report(abs(best[1] - z_rule) / z_rule < 0.12, "damper damping rule vs brute-force search", "best %.3f, rule %.3f" % (best[1], z_rule))

# ---------------------------------------------------------------- 4. every page call returns valid JSON without an error
base = {"N": 8, "h": 3.2, "m": [3e5] * 8, "k": [4e8] * 8, "system": "frame", "zeta": 0.05, "EI": 3e12, "ag": 0.05}
st = [{"name": "A", "lat": 24.9, "lon": 56.2}, {"name": "B", "lat": 24.45, "lon": 54.38}, {"name": "C", "lat": 25.29, "lon": 51.53}, {"name": "D", "lat": 23.59, "lon": 58.41}]
quake = {"lat": 27.7, "lon": 55.2, "mag": 6, "stations": st, "cities": st, "show": 0}
calls = [("analyse", base), ("design_stiffness", base), ("design_tmd", {"p": base, "target": 0.4}), ("design_isolation", {"p": base, "T": 2.5}),
         ("calibrate", {"p": base, "T": 1.2}), ("damage", {"p": base, "T": 1.1}), ("regression", {"h": [10, 20, 30, 40, 50, 60], "T": [0.4, 0.7, 1.0, 1.3, 1.6, 1.8]}),
         ("euler", base), ("race", base), ("det", base), ("verify", {}), ("detect", quake), ("tmd_rule", {"mu": 0.03}),
         ("record", {"x": ns["synth_seismogram"](200, 6)["x"], "fs": 20}), ("seismometer", {"f0": 1, "zeta": 0.7, "freqs": [0.5, 1, 2]})]
variants = {"1 storey": dict(base, N=1, m=[3e5], k=[4e8]), "40-storey frame": dict(base, N=40, m=[3e5] * 40, k=[4e8] * 40),
            "wall only": dict(base, N=30, m=[4e5] * 30, k=[3e8] * 30, system="wall"), "frame + core": dict(base, N=30, m=[4e5] * 30, k=[3e8] * 30, system="dual"),
            "bracing": dict(base, brace={"on": True, "A": 0.004, "bay": 6}), "floor dampers": dict(base, visc={"on": True, "c": 5e6}),
            "soft storey": dict(base, k=[1e8] + [4e8] * 7)}
for label, v in variants.items():
    calls += [("analyse", v), ("race", v), ("euler", v), ("det", v)]
for name, arg in calls:
    r = call(name, arg)
    report(not (isinstance(r, dict) and "error" in r), "page call: " + name, r.get("error", "") if isinstance(r, dict) else "")
d = call("detect", quake)
report(d["epi"] is not None and d["epi"]["err_km"] < 10, "detection pipeline finds the planted epicentre", "error %.2f km" % d["epi"]["err_km"])

# ---------------------------------------------------------------- 5. bugs that were fixed stay fixed
# The damper design used to say "not reachable" when the smallest damper already beat the target.
for zeta, target in ((0.05, 0.1), (0.01, 0.4), (0.005, 0.6)):
    r = call("design_tmd", {"p": dict(base, zeta=zeta), "target": target})
    report("error" not in r and r["smallest"] and r["peak"] / r["peak0"] <= 1 - target,
           "damper design: an easy target (damping %g%%, cut %g%%) gives the smallest damper, not an error" % (zeta * 100, target * 100), r.get("error", ""))
r = call("design_tmd", {"p": dict(base, zeta=0.10), "target": 0.6})
report("not reachable" in r.get("error", "") and len(r["curve"]) == 4, "damper design: an impossible target is reported as not reachable", r.get("error", "no error"))
# A lightly damped resonance peak is narrower than the coarse scan; the refined search must still find its top.
lite = dict(base, zeta=0.005); m0 = ns["build"](lite); f1 = m0["w_ref"] / (2 * math.pi)
fine = max(ns["roof_amp"](m0, *ns["harmonic_solve"](m0["M"], m0["C"], m0["K"], -m0["M"], 2 * math.pi * f1 * (0.97 + 0.06 * i / 3000))) for i in range(3001))
found = ns["peak_near_mode"](m0, f1, 1.0)
report(abs(found - fine) / fine < 2e-3, "peak search matches a 3001-point scan at 0.5% damping", "found %.6g, scan %.6g" % (found, fine))
# Messages the page shows must be plain words, never a Python exception name.
plain = [("damage: period far too long", "damage", {"p": base, "T": 60.0}), ("damage: period not longer", "damage", {"p": base, "T": 0.0}),
         ("regression: identical heights", "regression", {"h": [10, 10, 10, 10], "T": [1, 1, 1, 1]}),
         ("regression: too few rows", "regression", {"h": [10, 20], "T": [1, 2]}),
         ("regression: a negative height", "regression", {"h": [-10, 20, 30], "T": [1, 2, 3]}),
         ("record: empty", "record", {"x": [], "fs": 20}), ("record: repeated times", "record", {"t": [0, 0, 0], "x": [1, 2, 3], "fs": 20}),
         ("record: times going backwards", "record", {"t": [0, 1, 0.5, 2, 3], "x": [1, 2, 3, 4, 5], "fs": 20}),
         ("record: zero sample rate", "record", {"x": [1, 2, 3], "fs": 0}),
         ("record: a missing value", "record", {"t": [0, 1, 2], "x": [1, None, 3], "fs": 20}),
         ("record: time column in milliseconds", "record", {"t": [i * 20.0 for i in range(3000)], "x": [0.0] * 3000, "fs": 50})]
for label, name, arg in plain:
    r = call(name, arg)
    report("error" in r and not crashed(r), "plain message for " + label, r.get("error", "no error returned"))
r = call("regression", {"h": [10, 20, 10, 20, 10, 20], "T": [1, 2, 1.1, 2.1, 0.9, 1.9]})
report("error" not in r and "holdout" not in r, "regression: hold-out test is skipped when its half of the rows has one height", r.get("error", ""))
r = call("damage", {"p": dict(base, brace={"on": True, "A": 0.004, "bay": 6}), "T": 1.0})
report("error" not in r and r["exact"] is None, "damage: no 'exact' answer is claimed when bracing is not scaled", r.get("error", ""))
wall = dict(variants["wall only"], brace={"on": True, "A": 0.004, "bay": 6})
r = call("damage", {"p": wall, "T": 1.2 * ns["period_of"](wall)})
report("error" not in r and r["exact"] is not None and abs(r["alpha"] - r["exact"]) < 1e-6, "damage: a wall has no bracing in the model, so the exact answer still applies", r.get("error", ""))
line = [{"name": "A", "lat": 24, "lon": 52}, {"name": "B", "lat": 24, "lon": 54}, {"name": "C", "lat": 24, "lon": 56}]
r = call("detect", dict(quake, stations=line, cities=line))
report("error" not in r and r["epi"] is None and "line" in (r["epi_note"] or ""), "detection: three stations in a line give a note, not a crash", r.get("error", ""))
# A sensor can repeat a timestamp now and then; that must not reject the whole recording.
t = [i * 0.02 for i in range(2000)]; t[500] = t[499]
r = call("record", {"t": t, "x": [math.sin(i) * (5 if i > 1500 else 0.01) for i in range(2000)], "fs": 50})
report("error" not in r and r["tP"] is not None and abs(r["tP"] - 30.0) < 0.5, "record: one repeated timestamp is dropped and the trigger still fires", r.get("error", ""))
# Euler used to overflow to inf/NaN on tall buildings; every run must now stay finite.
for label in ("40-storey frame", "wall only", "frame + core"):
    r = call("euler", variants[label])
    flat = [v for run in r["runs"] for v in run["energy"] + run["roof"]]
    report(all(v is not None for v in flat) and len(r["exact"]) == 401, "Euler demo stays finite: " + label,
           "stopped at %s s" % [run["stopped"] for run in r["runs"]])

# ---------------------------------------------------------------- 6. the corners of the slider ranges
def nulls(o):
    """Count JSON nulls, which is what a NaN or an infinity becomes on its way to the page."""
    if o is None: return 1
    if isinstance(o, dict): return sum(nulls(v) for v in o.values())
    if isinstance(o, list): return sum(nulls(v) for v in o)
    return 0

def building(N, system, mass, stiff, EI, h, extras=()):
    q = {"N": N, "h": h, "m": [mass * 1000.0] * N, "k": [stiff * 1e6] * N, "system": system, "EI": EI * 1e9, "zeta": 0.05, "ag": 0.05,
         "brace": {"on": "brace" in extras, "A": 0.004, "bay": 6}, "iso": {"on": "iso" in extras, "kb": 2e7, "mb": mass * 1000.0, "zb": 0.15},
         "tmd": {"on": "tmd" in extras, "mu": 0.03, "f": 0.97, "zd": 0.1}, "visc": {"on": "visc" in extras, "c": 5e6}, "npts": 60, "cond": True}
    if "uneven" in extras and N > 1:
        q["m"][-1] *= 4; q["k"][0] *= 0.1
    return q

corners = [("1 light soft storey", building(1, "frame", 50, 20, 100, 2.6)), ("1 heavy stiff storey, all devices", building(1, "frame", 1000, 2000, 100, 5, ("iso", "tmd", "visc", "brace"))),
           ("2-storey wall", building(2, "wall", 50, 20, 100, 2.6)), ("40 heavy soft storeys", building(40, "frame", 1000, 20, 100, 5)),
           ("40-storey wall, weakest core", building(40, "wall", 1000, 20, 100, 5)), ("40-storey wall, stiffest core", building(40, "wall", 50, 2000, 10000, 2.6)),
           ("40-storey frame + core, all devices", building(40, "dual", 400, 300, 3000, 3.2, ("iso", "tmd", "visc", "brace"))),
           ("uneven 12-storey frame, isolated", building(12, "frame", 300, 400, 3000, 3.2, ("uneven", "iso"))),
           ("uneven 20-storey frame + core with damper", building(20, "dual", 300, 400, 3000, 3.2, ("uneven", "tmd")))]
for label, q in corners:
    r = call("analyse", q)
    if "error" in r:
        report(False, "corner: " + label, r["error"]); continue
    T = [m["T"] for m in r["modes"]]
    expected_nulls = (r["base"] is None) + (r["tmd"] is None)
    ok = nulls(r) == expected_nulls and all(T[i] >= T[i + 1] * (1 - 1e-9) for i in range(len(T) - 1)) and len(r["sweep"]["amp"]) == len(r["freqs"])
    report(ok, "corner: " + label, "periods %s, %d unexpected NaN/inf" % (np.round(T, 3), nulls(r) - expected_nulls))
    for name, arg in (("design_stiffness", q), ("design_isolation", {"p": q, "T": 2.5}), ("calibrate", {"p": q, "T": 1.2}), ("damage", {"p": q, "T": 1.5 * T[0]})):
        r2 = call(name, arg)
        report(not crashed(r2), "corner: " + label + " -> " + name, r2.get("error", "") if isinstance(r2, dict) else "")

# ---------------------------------------------------------------- 7. the page and its script agree
script = html[html.index('<script>\n"use strict";'):]
ids = set(re.findall(r'\bid="([^"${}]+)"', html))
used = set(re.findall(r'\$\("([\w-]+)"\)', script)) | set(re.findall(r'onClick\("([\w-]+)"', script))
slider_ids = re.findall(r'"(\w+)"', re.search(r"const IDS = \[(.*?)\]", script).group(1))
tabs = re.findall(r'"(\w+)"', re.search(r"const TABS = \[(.*?)\]", script).group(1))
used |= set(slider_ids) | {"v" + s for s in slider_ids} | {"t-" + t for t in tabs} | {"tab-" + t for t in tabs}
report(used <= ids, "every element the script looks up exists in the page", "missing: %s" % sorted(used - ids) if used - ids else "%d ids" % len(used))
state = re.search(r"const S = \{(.*?)\};", script, re.S).group(1)
report(all(re.search(r"\b%s:" % s, state) for s in slider_ids), "every slider has a starting value in the state")
api_names = set(re.findall(r'name == "(\w+)"', src))
js_calls = set(re.findall(r'solver\.(?:call|must)\("(\w+)"', script))
report(js_calls <= api_names, "every solver call the page makes exists in api()", "missing: %s" % sorted(js_calls - api_names) if js_calls - api_names else ", ".join(sorted(js_calls)))
label_for = set(re.findall(r'<label for="([\w-]+)"', html))
report(label_for <= ids, "every label points at a control that exists", "missing: %s" % sorted(label_for - ids))
controls = set(re.findall(r'<(?:input|select|textarea)\b[^>]*\bid="([\w-]+)"', html))
wrapped = set(re.findall(r'<label class="chk"><input type="checkbox" id="([\w-]+)"', html))
named = set(re.findall(r'<(?:input|select|textarea)\b[^>]*\bid="([\w-]+)"[^>]*aria-label=', html))
report(controls <= label_for | wrapped | named, "every control has a label", "unlabelled: %s" % sorted(controls - label_for - wrapped - named))
canvases = re.findall(r"<canvas\b[^>]*>", html)
# A canvas must give its height as data-h. With a height attribute the drawing code would read back a value
# it had already multiplied by the screen's pixel ratio, and every chart would grow on each redraw.
report(len(canvases) >= 15 and all('data-h="' in c and " height=" not in c and "aria-label=" in c for c in canvases),
       "every canvas gives its height as data-h and has a text description", "%d canvases" % len(canvases))
readme = (ROOT / "README.md").read_text(encoding="utf-8")
claimed = re.search(r"\| 5 · Verify \| (\d+) checks", readme)
report(bool(claimed) and int(claimed.group(1)) == len(checks), "README states the real number of verification checks",
       "README says %s, the solver runs %d" % (claimed.group(1) if claimed else "nothing", len(checks)))

print("\n%d failed" % fails)
sys.exit(1 if fails else 0)
