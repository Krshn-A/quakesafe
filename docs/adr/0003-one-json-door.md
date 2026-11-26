# ADR-0003: One JSON door between the page and the solver

**Status:** Accepted (the app was built this way; this records why)
**Date:** 2026-11-26
**Deciders:** project author

## Context

The page script is JavaScript and the solver is Python. They need a way to call each other. Pyodide can hand Python objects to JavaScript directly through proxies, or the two sides can exchange text. The solver also has to run in plain Python, outside a browser, so that it can be tested.

## Decision

The solver exposes exactly one function to the page:

```python
api(name: str, payload: str) -> str
```

Both strings are JSON. `api` picks the Python function by `name`, catches any exception and returns it as `{"error": "..."}`, and passes the result through `_clean`, which turns numpy arrays into lists, NaN and infinity into `null`, and rounds numbers to 7 significant figures.

## Options considered

### Option A: one function, JSON text both ways (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Cost | Encoding and decoding on every call (a few milliseconds for the largest result) |
| Scalability | Fine up to results of a few megabytes |
| Team familiarity | High |

**Pros:** the solver has no browser code in it, so `test_solver.py` calls the very same `api` from plain Python; text crosses the worker boundary without any special handling; one place catches errors; one place cleans numbers.
**Cons:** no type checking of arguments or results; a mistyped field name shows up only when that feature is used.

### Option B: Pyodide proxies (call Python functions and read numpy arrays from JavaScript)

| Dimension | Assessment |
|---|---|
| Complexity | Medium: proxies must be converted and destroyed by hand |
| Cost | Fastest for large arrays |
| Scalability | Best for big data |
| Team familiarity | Low |

**Pros:** no encoding; arrays could be shared without copying.
**Cons:** proxies cannot be sent out of a worker, so this would not work with ADR-0002 without extra conversion; memory leaks if a proxy is not destroyed; the solver could no longer be tested the same way outside the browser.

### Option C: one message type per feature, with a written schema

| Dimension | Assessment |
|---|---|
| Complexity | High for 15 calls |
| Cost | A schema to keep up to date |
| Scalability | Best for a team |
| Team familiarity | Low |

**Pros:** mistakes in field names are caught early.
**Cons:** more to maintain than the project needs.

## Trade-off analysis

The largest result is the analysis of a 42-degree-of-freedom system with about 190 frequencies: roughly 16,000 numbers, well under a megabyte of JSON. Encoding it costs far less than computing it. So speed is no reason to prefer proxies, and JSON keeps the solver free of anything to do with browsers. The missing type checks are covered in part by tests: every call is exercised through `api`, and the test script fails if the page calls a name that `api` does not have.

## Consequences

- Any Python function can be offered to the page with one line in `api`.
- The page must treat `null` as "no number" everywhere. `fmt` prints it as "–" and `plot` skips it.
- Numbers shown in the page have at most 7 significant figures.
- A message that starts with a Python exception name means a bug; the tests look for that pattern.
- Revisit if results grow past a few megabytes, or if several people work on the two sides and field names start to drift.

## Action items

1. [x] Keep the list of calls in [ARCHITECTURE.md](../ARCHITECTURE.md) section 4 up to date.
2. [x] Test that every call the page makes exists in `api`.
