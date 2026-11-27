# SynkAI — "The AI Boardroom Copilot" — Design System & Storyboard

A marketing landing site for SynkAI. The visitor enters a boardroom: frosted
doors part, the camera walks the table, lights come up, and the table
surface becomes a hologram that tells the product's story. Direction: quiet
luxury, executive, nocturnal. Nothing bouncy — motion is slow, weighty,
cinematic, and scroll is the only director.

## 1. Colour

Nocturnal palette. Brass is the luxury accent (used for structure, rules,
etched type). Cyan is reserved **only** for anything intelligent — AI
insights, the hologram, tags, highlighted data. Mixing the two dilutes both,
so cyan never appears as decoration and brass never appears on data.

| Token              | Hex       | Use                                             |
| ------------------ | --------- | ----------------------------------------------- |
| `--c-obsidian`     | `#07080A` | page background, deepest shadow                 |
| `--c-obsidian-2`   | `#0C0E12` | panel background, card fill                     |
| `--c-graphite`     | `#15181D` | raised surface, table wood-stone base           |
| `--c-graphite-2`   | `#1E2229` | borders, dividers, chair/table shading          |
| `--c-ivory`        | `#F3EFE6` | primary text (warm white, not pure white)       |
| `--c-ivory-dim`    | `#B9B4A8` | secondary text                                  |
| `--c-ivory-faint`  | `#726E64` | tertiary / disabled text                        |
| `--c-brass`        | `#C9A467` | accent rules, etched headline strokes, buttons  |
| `--c-brass-bright` | `#E7C98B` | brass hover / highlight state                   |
| `--c-signal`       | `#5FE1E0` | AI signal cyan — insights, hologram, tags only  |
| `--c-signal-dim`   | `#2C8C8C` | cyan at rest / low emphasis                     |
| `--c-risk`         | `#E2795C` | risk tag only (muted terracotta, not alarm red) |
| `--c-good`         | `#8FD6A6` | "done" / resolved state only                    |

Contrast checked against `--c-obsidian` (#07080A):

- `--c-ivory` on obsidian: ~16.9:1 (AAA)
- `--c-ivory-dim` on obsidian: ~8.1:1 (AAA)
- `--c-brass` on obsidian: ~8.4:1 (AAA) — safe for body-sized UI text, not just large type
- `--c-signal` on obsidian: ~11.6:1 (AAA)
- `--c-ivory-faint` on obsidian: ~4.6:1 — large/supporting text only, never body copy

## 2. Type

- **Display** — Fraunces (serif, large optical size, tight tracking). Editorial
  headlines, section titles, the door etching, the footer wordmark.
- **UI / body** — Inter. All paragraph copy, labels, nav, buttons, form.
- **Mono** — JetBrains Mono. Transcript lines, timestamps, task metadata,
  anything that reads as "data" or "system output."

Scale (desktop → mobile clamp):

- Display XL: `clamp(2.75rem, 7vw, 6.5rem)`, leading 0.98, tracking -0.02em
- Display L: `clamp(2.25rem, 4.5vw, 4rem)`, leading 1.02
- Display M: `clamp(1.5rem, 2.6vw, 2.25rem)`
- Body L: `1.125rem` / 1.6
- Body: `1rem` / 1.6
- Label / mono: `0.8125rem`, tracking 0.04em, uppercase for labels only

## 3. Spacing & grid

8px base unit. Section vertical rhythm: `clamp(5rem, 12vw, 9rem)` top/bottom
padding. Content max-width `1200px`, side gutter `clamp(1.25rem, 5vw, 4rem)`.
Cards use 1px hairline borders (`--c-graphite-2`) over `--c-obsidian-2`, never
heavy drop shadows — light is the only thing allowed to "glow" (box-shadow
used solely to simulate brass/cyan light bleed).

## 4. Motion tokens

- Ease (default): `power2.out` for entrances, `power1.inOut` for scroll-scrub.
  No `elastic`, `bounce`, or `back` eases anywhere.
- Durations: micro `0.25s`, standard `0.6s`, slow `1.1s`, cinematic `1.8s+`
  (reserved for the doors and the room pull-back).
- Scroll is the primary driver: pinned sections scrub 1:1 with scroll
  position rather than playing on a timer. Nothing auto-plays off a clock
  except the preloader and small looping details (waveform, chime pulse).
- `prefers-reduced-motion: reduce` turns off: Lenis smooth scroll, all
  ScrollTrigger pins/scrubs, the preloader, and WebGL — replaced by normal
  native scroll, static reveal-on-view fades (opacity only, 0.4s), and a
  static illustrated boardroom still.

## 5. Shot-by-shot storyboard

1. **Preloader** — obsidian field, a 1px brass line fills left→right over
   ~1.1s with a tiny numeric counter (00→100). Skippable (tap/click or any
   key). Never shown on repeat visits in-session or under reduced motion.
2. **The Doors** — full-bleed frosted double doors, "SynkAI" etched centre.
   Headline: "Every decision starts in the room." Pinned ~100vh; scroll
   drives the doors apart (translateX) and warm light bleeds through the
   gap, fading to the room beyond.
3. **The Walk-in** — Three.js. Camera dollies down a long table; ceiling
   light strips switch on in sequence just ahead of the camera; a glass wall
   shows a night skyline of instanced emissive windows. Overlay copy:
   "SynkAI. The AI Boardroom Copilot."
4. **The table comes alive** — camera settles and tilts toward the tabletop;
   a cyan hologram ring materialises above the wood showing BEFORE → DURING →
   AFTER → FOLLOW-THROUGH → NEXT MEETING.
5. **BEFORE** — agenda + brief cards rise above the table.
6. **DURING** — mono-type live transcript (labelled illustrative), waveform,
   live tags (DECISION / RISK / QUESTION), "Ask Synk" sample Q&A.
7. **AFTER** — transcript fragments assemble into structured minutes +
   extracted action items.
8. **FOLLOW-THROUGH** — tasks slide into tracked columns (owner, deadline,
   reminder bell); one task flips overdue → done.
9. **NEXT MEETING** — camera pulls back to a wide shot; lights dim and come
   back: "The next meeting begins where the last one ended."
10. **Under the hood** — calm, static (non-pinned) section: local-first AI,
    RAG, and an animated multi-agent diagram (parser → summary/action/
    decision/deadline/risk agents → coordinator).
11. **CTA** — "Request early access" form (email + optional company),
    honeypot, posts to a SvelteKit form action → Google Apps Script webhook.
12. **Footer** — oversized SynkAI wordmark, minimal links.

## 6. Engineering notes

- One Three.js canvas is shared across shots 3–9 ("the room journey"), pinned
  for the duration of a single tall scroll track; camera position/rotation
  and light intensities are driven by a single `progress` value (0–1) read
  from one `ScrollTrigger`. HTML overlays for shots 5–8 are plain DOM,
  cross-faded in/out by the same progress value — not separately pinned.
- Doors (shot 2) and Under the hood / CTA / Footer (shots 10–12) are plain
  DOM + CSS/GSAP, no WebGL.
- Three.js is dynamically imported on mount, after first paint, in its own
  chunk. DPR capped at 1.75. Render loop pauses on `visibilitychange` and
  when the canvas leaves the viewport (`IntersectionObserver`). Full
  dispose of geometries/materials/renderer on unmount.
- Mobile: the room journey keeps the same beats but with fewer chairs/
  windows, a shorter scroll track, and a lower DPR cap (1.25).
