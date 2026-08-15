# JurisTwin Sentinel — JurisTech Brand Edition v5.2

## Design objective

The v5.2 interface is designed for a short live final where judges must understand the product before they understand the architecture. It uses the public JurisTech website as a visual-direction reference: generous white space, large black headlines, strong red calls to action, concise benefit-led copy, and high-contrast product storytelling. It does not copy JurisTech website assets or claim to be an official JurisTech product.

## Visual system

- Primary background: warm white / soft grey.
- Primary text: near-black.
- Primary brand/action signal: Juris red.
- Safe state: green.
- Evidence/analysis secondary signal: teal.
- Dark surfaces are reserved for the two places where contrast adds meaning: the live conflict network and decision certificates/results.
- Rounded forms are restrained; the application avoids turning every data point into a decorative card.

## Readability

Default type is intentionally larger than v5.1:

- Judge-facing hero: 46–70 px depending on viewport.
- Hero explanation: 17 px.
- KPI values: 44 px.
- Navigation: 14 px.
- Primary controls: 14 px.
- Main workflow copy: 15–17 px.

Presentation Mode (`Alt + P`) increases supporting copy and controls for low-resolution projectors without changing the layout or browser zoom.

## Information architecture

The five primary destinations remain:

1. Overview
2. Conflict Map
3. Digital Twin
4. Assurance
5. Evidence Lab

The full pitch-deck feature set is preserved through progressive disclosure under the **Platform** action:

- Secure Enterprise Memory
- Living Decision Digital Twin
- White-Box Future Simulator
- AI Bodyguard
- Decision Ledger
- Enterprise Connectors
- Policy Reasoner

This prevents the finals interface from becoming a dense feature catalogue while keeping every implemented capability directly demonstrable.

## Interaction principles

- Native document scrolling; no locked dashboard viewport.
- Sticky sidebar and sticky command bar.
- One primary action per screen.
- Native View Transitions where supported.
- Reusable side-sheet system for secondary technical proof.
- X, Escape and backdrop close paths remain shared across sheets.
- Conflict graph keeps pointer capture and bounded node positions.
- One non-stacking status capsule for action feedback.
- Reduced-motion preferences remain respected.

## Judge-first demo principle

The first visible layer answers only four questions:

1. What is wrong?
2. Who is affected?
3. What should we do?
4. Can we prove the decision is safe?

Architecture, cryptographic evidence, connector state, memory search and security actions are available immediately when a judge asks for technical depth.
