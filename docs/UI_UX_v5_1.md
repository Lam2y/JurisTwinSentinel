# JurisTwin Sentinel — JurisTech v5.1 UI/UX

## Design intent
The finals interface is designed as a premium legal/decision-intelligence workspace rather than a generic dashboard. The visual language is deliberately restrained: obsidian/navy surfaces communicate seriousness, evidence cyan communicates intelligence/provenance, green communicates safe state, red communicates contradiction, and judicial gold is reserved for authority and governance cues.

## Native page scrolling
Desktop now uses normal document scrolling. The sidebar and command header remain sticky while content moves naturally beneath them. Mouse wheel, trackpad, Page Up/Down, scrollbar dragging, keyboard navigation and browser accessibility therefore work without a nested hidden scroll container.

## Motion system
- Browser View Transitions when supported, with CSS fallback.
- Short content-first reveal animations rather than decorative looping animation.
- Pointer-reactive ambient evidence light is throttled through requestAnimationFrame.
- A two-pixel scroll progress rail gives orientation on longer evidence/graph pages.
- `prefers-reduced-motion` disables non-essential motion.

## Finals hierarchy
The primary navigation remains deliberately limited to five destinations:
1. Overview
2. Conflict Map
3. Digital Twin
4. Assurance
5. Evidence

Each screen leads with one large judgement-relevant statement and one dominant next action. Technical detail remains progressively disclosed through the side sheet.

## Responsive behavior
- Native document scroll on desktop and mobile.
- Sticky application chrome on larger displays.
- Sidebar collapses at medium widths and hides on narrow screens.
- Graph canvas remains self-contained; nodes retain pointer capture and boundary clamping.
- Sheets become full-width on narrow displays.
