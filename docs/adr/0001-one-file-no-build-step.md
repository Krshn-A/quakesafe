# ADR-0001: One file, no build step

**Status:** Accepted (the app was built this way; this records why, and when to change)
**Date:** 2026-11-26
**Deciders:** project author

## Context

QuakeSafe is a course project that is handed in as a link and as source. It is hosted on GitHub Pages, maintained by one person, and has to stay readable by someone who knows Python and a little HTML. At the time of writing `index.html` is about 2,100 lines: 330 of markup and styles, 1,100 of Python, 20 for the worker and 660 of JavaScript.

## Decision

Keep the whole app in `index.html`: markup, styles, the Python solver, the worker source and the page script. No bundler, no package manager, no generated files. The only thing fetched at run time is Pyodide, from a CDN, at a pinned version.

## Options considered

### Option A: one file (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Low. Edit, reload. |
| Cost | None |
| Scalability | Poor past a few thousand lines |
| Team familiarity | High |

**Pros:** nothing to install; "view source" shows everything; cannot get out of step with itself; easy to hand in and to host.
**Cons:** the JavaScript cannot be imported by a test runner; one long file; a service worker (for offline use) is not possible, because it must be its own file.

### Option B: separate files, no build (`index.html`, `solver.py`, `app.js`, `styles.css`)

| Dimension | Assessment |
|---|---|
| Complexity | Low to medium |
| Cost | None |
| Scalability | Better |
| Team familiarity | High |

**Pros:** each file has one language, so editors and linters work better; `solver.py` can be imported directly by tests; `app.js` could be unit-tested.
**Cons:** the page must fetch `solver.py` before it can start, which adds a failure case; four files to keep in step; "the whole app is one file" stops being true.

### Option C: a bundler (Vite or similar) with a `src/` folder

| Dimension | Assessment |
|---|---|
| Complexity | High for this project |
| Cost | Node.js tool chain to install and keep working |
| Scalability | Best |
| Team familiarity | Low |

**Pros:** modules, type checking, unit tests, minified output.
**Cons:** a build step between the source and the page; generated files to deploy; far more machinery than about 700 lines of JavaScript need.

## Trade-off analysis

The app is small and has one maintainer. The main cost of one file is that the JavaScript has no unit tests. That is reduced, not removed, by two things: all numerical work is in Python, which is tested directly out of the same file; and `test_solver.py` checks the wiring statically (ids, call names, labels, canvas heights). Option B would buy JavaScript unit tests at the price of a second failure case at start-up. Option C is not justified at this size.

## Consequences

- Changing the app stays as simple as editing one file.
- Page-script bugs can only be caught by the static checks or by hand in a browser (see [TESTING.md](../TESTING.md)).
- No offline use.
- Revisit when the page script passes about 1,000 lines, or when a second person starts working on it. Option B is the next step.

## Action items

1. [x] Keep the three script blocks clearly separated and commented inside `index.html`.
2. [x] Check the page's wiring from `test_solver.py`.
3. [ ] Add an automated browser test (see TECH_DEBT.md, item 3).
