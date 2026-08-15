# Championship v5 UI/UX

v5 is a ground-up finals-interface refactor. The backend workflows remain intact; the presentation layer was rebuilt around judge comprehension, reliability and responsive interaction.

## What was removed

- Fixed 1440×1024 prototype staging.
- Legacy static screen HTML files.
- Stacked notification rectangles.
- Dense navigation with ten screens.
- Multiple one-off modal implementations.
- Decorative card walls that did not help the demo story.

## Current interaction model

### Five-screen information architecture

Overview → Conflict map → Digital twin → Assurance → Evidence.

Secondary functions appear only in context through a side sheet. This keeps first-view information density low.

### Motion

- Native View Transitions API for route changes where the browser supports it.
- Short staggered content entrance animation.
- Hover/press states that do not move layout.
- Reduced-motion support through `prefers-reduced-motion`.

### One side-sheet primitive

Every secondary panel uses the same component and closes through:

- the top-right X button;
- the `Esc` key;
- clicking the backdrop;
- explicit Cancel actions.

This removes the inconsistent close-button behavior from earlier builds.

### Single status capsule

Only one transient status message can exist at a time. New status replaces old status instead of stacking rectangular toasts in the bottom-right corner.

## Conflict graph reliability

The evidence graph uses one SVG viewBox (`0 0 1000 620`) that scales to the available browser area.

Every node:

- is draggable;
- uses pointer capture for fast mouse movement;
- has text with pointer events disabled so labels cannot block dragging;
- is clamped using its actual node dimensions;
- cannot move outside the visible SVG canvas;
- keeps all connected edges updated during drag;
- remains keyboard-selectable.

Because positions are stored in viewBox coordinates, resizing the browser does not push nodes off-screen.

## Projector behavior

At 1024px width the sidebar collapses to icons, while the primary overview still retains the four-metric strip and the two-column focal layout. More aggressive vertical stacking only begins below 900px.

## Finals design principle

Every screen should answer one judge question immediately:

- Overview — **What is wrong?**
- Conflict map — **Why is it wrong?**
- Digital twin — **What should we do?**
- Assurance — **Can we trust the change?**
- Evidence — **Does it work on something you did not prepare?**
