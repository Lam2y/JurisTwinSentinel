# JurisTwin Finals Frontend — v5.3

The Grand Finals interface is a **zero-build responsive single-page application** designed for deterministic stage use. It deliberately has no npm/runtime dependency: `run_finals.bat` starts FastAPI and serves the tested frontend from `backend/app/static`.

## v5.3 design direction

- JurisTech-inspired white / black / red visual hierarchy.
- Large projector-safe typography.
- Native document scrolling with sticky application chrome.
- Selective dark analytical canvases instead of an all-dark dashboard.
- Native View Transitions API when supported.
- Pointer-captured SVG graph dragging with viewport bounds.
- One reusable side-sheet primitive for secondary proof and every close path.
- `Platform` progressive-disclosure drawer preserving all pitch-deck capabilities.
- Presentation Mode (`Alt + P`) for additional projector readability.
- One non-stacking status capsule instead of toast clutter.
- All API writes remain handled by the existing FastAPI governance layer.

`frontend/src` is the readable source mirror. The deployable copies live in `backend/app/static` so one Python command serves the complete product.
