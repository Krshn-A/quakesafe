# ADR-0002: The solver runs in a web worker

**Status:** Accepted
**Date:** 2026-11-26
**Deciders:** project author

## Context

The solver is Python running in the browser through Pyodide. It used to run on the page's own thread: every call froze the page until it returned. Measured on a laptop, one analysis took 0.37 s for the 8-storey preset and 1.8 s for a 40-storey frame + core building, and one ran after every slider movement. Detection ran on every slider event with no delay at all (about 0.12 s each). Phones are several times slower. While frozen, the page cannot animate, scroll or respond, and the browser may offer to close it.

## Decision

Run Pyodide and the solver in a web worker. The worker's source is a `<script type="text/js-worker">` block in `index.html`, started from a Blob URL, so the app stays one file (ADR-0001). The page script sends `{name, payload}` messages and gets JSON text back; calls return promises. For slider-driven calls, requests made while one is running collapse into a single re-run with the newest values.

## Options considered

### Option A: stay on the page's thread

| Dimension | Assessment |
|---|---|
| Complexity | Lowest: plain function calls |
| Cost | None |
| Scalability | Bad: freezes grow with building size and on slow devices |
| Team familiarity | High |

**Pros:** simplest code; result and state always match.
**Cons:** freezes of up to about 2 s on a laptop per slider step; much longer on a phone.

### Option B: page's thread, but coarse while dragging and fine on release

| Dimension | Assessment |
|---|---|
| Complexity | Medium: two kinds of result to draw |
| Cost | None |
| Scalability | Medium: shorter freezes, still freezes |
| Team familiarity | High |

**Pros:** no asynchronous code.
**Cons:** still freezes; verification (2.5 s) and the lab still block; the charts jump when the fine result arrives.

### Option C: web worker (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Medium: every call is asynchronous |
| Cost | None |
| Scalability | Good: compute time no longer affects how the page feels |
| Team familiarity | Medium |

**Pros:** the page never freezes (longest pause measured: 18 ms during a drag that used to freeze for 1.8 s per step); Pyodide's start-up does not block either; a crashed solver can be restarted without reloading.
**Cons:** results arrive later than the click, so a result can describe a slightly older state; start-up and call failures need their own handling; a worker cannot check the integrity hash of the script it imports.

## Trade-off analysis

The cost of the worker is asynchronous code. It is contained in one place: the `solver` object with `call` and `must`, the `job` wrapper that shows "Computing…" and locks the button, and `latest` for slider-driven work. The rest of the page script reads almost as before, with `await` in front of each call. The risk of drawing a result that no longer matches the sliders is handled by the worker answering in order and by `latest` always finishing with the newest values. Option B was rejected because it keeps the freeze and adds a second code path.

## Consequences

- Sliders, scrolling and the animation stay smooth while Python works.
- A button stays locked while its own call runs, so it cannot be pressed twice.
- If Pyodide cannot load, the page says why and offers **Try again**.
- The lab shows a note when the building has changed since its last run, because its results no longer appear instantly with the building.
- Opening `index.html` straight from the disk (a `file://` address) has not been tested with the worker; use a local web server.
- Revisit if a single call needs to be cancelled mid-way. At present a long call can only be abandoned by restarting the worker.

## Action items

1. [x] Move Pyodide into a Blob worker; one `api` call per message.
2. [x] Make slider-driven calls collapse to the newest request.
3. [x] Show load failures with a retry button.
4. [ ] Test on a real phone (see TECH_DEBT.md, item 1).
