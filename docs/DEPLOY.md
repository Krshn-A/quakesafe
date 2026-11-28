# Putting a new version live

The live page is https://krshn-a.github.io/quakesafe/. GitHub Pages serves whatever is at the root of the `main` branch, so **a push to `main` is a deploy**. It takes about a minute, and browsers may keep the old page for up to ten minutes.

There is no staging site, no database and no feature flags. The checks below stand in for them.

## Before

Work on a branch, never on `main`.

- [ ] `python test_solver.py` ends with `0 failed`.
- [ ] `python test_accuracy.py` ends with `0 failed`. If the solver changed, read the "worst" column: no number should have moved by more than a factor of ten without a reason you can state.
- [ ] `python test_mutants.py` ends with `0 missed, 0 stale`.
- [ ] If the Pyodide version changed: repeat the desktop-against-browser comparison of [ACCURACY.md](ACCURACY.md), section 5.
- [ ] The manual browser checklist in [TESTING.md](TESTING.md) has been done on the branch, served locally (`python -m http.server 8000`), at desktop width and at phone width.
- [ ] The browser console shows no errors after loading and after visiting every tab.
- [ ] The Verify tab reports every check passed. (This is the solver running in the browser's Python, which is not the Python the test scripts use.)
- [ ] Someone other than the author has read the diff. For a change to the solver, that includes the new lines of `test_accuracy.py` output.
- [ ] Nothing in the "Open items" table of [TECH_DEBT.md](TECH_DEBT.md) became worse.
- [ ] Write down the commit that is live now, so there is something to go back to:

  ```
  git fetch origin
  git rev-parse --short origin/main
  ```

## Deploy

- [ ] Push the branch and wait for the **tests** workflow to go green on GitHub (Actions tab).
- [ ] Move `main` forward to the branch. This must be a fast-forward; never force-push `main`.

  ```
  git push origin my-branch:main
  ```

- [ ] On GitHub, wait for **pages build and deployment** to finish.
- [ ] Open the live page with something after a `?` so the browser cannot use its copy, for example `https://krshn-a.github.io/quakesafe/?v=2`. Then check:
  - [ ] the status at the top right reaches "Ready";
  - [ ] the building is drawn and the three headline numbers are filled in;
  - [ ] the console is clean;
  - [ ] the Verify tab passes;
  - [ ] the page works on a phone.

## After

- [ ] Add a line to the release log below.
- [ ] Tell the repository owner and anyone who is about to hand the link in.

## When to go back

Go back at once if, on the live page, any of these is true:

- the status never reaches "Ready", or the box "The Python solver could not start" appears on a good connection;
- there is an error in the console on load;
- the Verify tab shows a failed check;
- the building or a chart is not drawn, or the layout is broken on a phone;
- a number on the Building tab for the default building differs from the last release for no stated reason. For the 8-storey apartment preset the natural period is **0.932 s**, the peak storey drift **0.71%** and the roof sway **29.5 mm**.

How: undo the bad commits with new commits and push those. Do not rewrite history on `main`.

```
git revert <first-bad-commit>^..<last-bad-commit>
git push origin HEAD:main
```

Pages redeploys in about a minute. Then check the live page again as above.

## What is not watched

Nothing watches the live page. There are no error reports and no visitor numbers. If Pyodide's CDN or Google Fonts is down, nobody is told; the page itself shows a message when Python cannot load. That is acceptable for a course project and is listed in TECH_DEBT.md.

## Release log

| Date | Commit on `main` | What changed | Checked on the live page by |
|---|---|---|---|
| 2026-11-26 | `92fbaaa` | First version | not recorded |
| 2026-11-26 | `d1160ef` | Chart-size bug fixed, solver in a worker, wider tests, docs, "Seismic Atlas" look | loaded to "Ready", building drawn, console clean (desktop browser only) |
| 2026-11-27 | `307d53d` | Accuracy audit: solver fixes, 87 built-in checks, accuracy and wrong-solver test scripts, page fixes, new docs | "Ready"; headline numbers 0.932 s, 0.71%, 29.5 mm; every tab visited with a clean console; Verify 87 of 87; phone width emulated in a desktop browser (no real phone) |
| 2026-11-28 | `3674372` | Drawings follow the sliders; the Detect tab's earthquake is linked to the building; the Lab fills itself; plainer words and a note under every chart | "Ready"; headline numbers unchanged (0.932 s, 0.71%, 29.5 mm); "At the building" filled in; the Lab filled without a button; Verify 87 of 87; clean console (desktop browser) |
| 2026-11-28 | `4112ca1` | Dark "Midnight" look: navy page, orange accent, pill tabs and buttons, lit windows, a legend under the building. No change to the solver or to any control | "Ready"; headline numbers unchanged (0.932 s, 0.71%, 29.5 mm); every tab visited with a clean console; Shake peak 137 mm at 1.07 Hz; the Lab filled; Verify 87 of 87 (desktop browser; phone width was emulated before the release, no real phone) |
