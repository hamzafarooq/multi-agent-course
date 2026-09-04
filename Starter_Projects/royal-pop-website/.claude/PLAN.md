# Royal Pop Landing Page — Build Plan

> Resumable plan. If restarting, read this file first, then check the **Status** section to see where to pick up.

## Product Identified

**Audemars Piguet × Swatch — Royal Pop Collection** (launched May 16, 2026)

- Bioceramic **pocket watch** collaboration (octagonal Royal Oak silhouette, Swatch POP-inspired loop strap)
- Eight colorful models — six **Lépine** style (crown at 12) and two **Savonnette** style (crown at 3, small seconds at 6)
- Powered by hand-wound **SISTEM51** movement (15 active patents)
- Bioceramic = 2/3 ceramic powder + 1/3 castor-oil-derived biosourced material
- **Pricing:** Lépine $400 USD · Savonnette $420 USD
- Distribution: selected Swatch boutiques only; 1 per person per store per day

Named models seen in search: LAN BA, BLAUE ACHT, OCHO NEGRO (+ five others).

### Local assets
- Video: `video/8887ad431858cde1fcfde38c3d45edcd_1779083229_lslzo3i4.mp4` — 1280×720, 15.04s, 24fps, 361 frames
- Images: `images/black.png`, `images/blue.png`, `images/yello.png` (pink/yellow/teal "tutti frutti" variant)

## Source References

- [Royal Pop Collection — Swatch.com](https://www.swatch.com/en-us/royal-pop.html)
- [Audemars Piguet × Swatch — Origins](https://www.audemarspiguet.com/com/en/news/origins/swatch-royal-pop.html)
- [Swatch Group announcement](https://www.swatchgroup.com/en/services/archive/2026/audemars-piguet-swatch)
- [Time+Tide — Introducing](https://timeandtidewatches.com/audemars-piguet-swatch-royal-pop-introducing/)
- [Notebookcheck — eight shades](https://www.notebookcheck.net/Swatch-x-Audemars-Piguet-Royal-Pop-pocket-watch-launches-with-eight-unique-shades.1295556.0.html)

## Skill in use

`.claude/skills/video-to-website.md` — premium scroll-driven site with frame-by-frame canvas playback, Lenis smooth scroll, GSAP timeline choreography. **Non-negotiable** checklist (Lenis, 4+ animation types, hero standalone 100vh, circle-wipe reveal, marquee, dark stats overlay, counters, side-aligned text, persistent CTA) lives in that skill file.

## Frame Extraction Math

- Source: 15.04s @ 24fps = 361 frames
- Target: extract at ~16fps → ~240 frames (in the 150–300 sweet spot per skill)
- Width: 1280 (no upscale needed)
- Command:
  ```bash
  cd "/Users/traversaal-001-hf/Dropbox/Mac (3)/Documents/Github/royal-pop-website"
  mkdir -p frames
  ffmpeg -i "video/8887ad431858cde1fcfde38c3d45edcd_1779083229_lslzo3i4.mp4" \
    -vf "fps=16,scale=1280:-1" -c:v libwebp -quality 80 \
    "frames/frame_%04d.webp"
  ls frames | wc -l
  ```

## Site Architecture

```
royal-pop-website/
├── .claude/
│   ├── PLAN.md                ← this file
│   └── skills/video-to-website.md
├── images/{black,blue,yello}.png   (model photos for content blocks)
├── video/...mp4
├── frames/frame_NNNN.webp     (generated)
├── index.html
├── css/style.css
└── js/app.js
```

Total scroll: **900vh** (8+ sections, hero gets 20%).

### Section map (data-enter / data-leave / data-animation)

| # | Section | Enter | Leave | Animation | Align | Notes |
|---|---------|-------|-------|-----------|-------|-------|
| Hero | "Royal Pop" — standalone 100vh, word-split heading, circle-wipe out | — | — | hero | center | Solid Bioceramic-cream bg `#f5f3f0` |
| 001 | The Pocket Watch, Reborn | 8 | 20 | `slide-left` | left | Heritage: Royal Oak 1972 × Swatch POP 1980s |
| 002 | Bioceramic | 22 | 34 | `slide-right` | right | 2/3 ceramic + 1/3 castor-oil biosourced |
| 003 | SISTEM51 — Hand-Wound | 36 | 48 | `clip-reveal` | left | 15 active patents |
| Stats | The Numbers | 52 | 66 | `stagger-up` | center w/ dark overlay | 8 models · 51 components · 15 patents · 1972 origin |
| 004 | Two Silhouettes (Lépine / Savonnette) | 68 | 78 | `rotate-in` | right | Crown at 12 vs 3 |
| 005 | Eight Shades | 80 | 88 | `scale-up` | left | Color marquee + named models |
| CTA | Find a Boutique | 92 | 100 | `fade-up` | center | `data-persist="true"` |

### Marquee
- One horizontal text marquee: `"ROYAL POP · ROYAL POP · ROYAL POP"` — 12vw, sliding `xPercent: -25` on scroll.
- Fades in 40%–60% scroll range.

### Color tokens

```css
--bg-light: #f5f3f0;     /* Bioceramic cream */
--bg-dark:  #111111;
--accent-orange: #ff5a1f; /* from blue/orange variant */
--accent-teal:   #2dd4bf;
--accent-pink:   #ff9ec7;
--text-on-light: #1a1a1a;
--text-on-dark:  #f0ede8;
--font-display: 'Fraunces', serif;  /* editorial pop */
--font-body:    'Inter', sans-serif;
```

## Build Steps (resumable checklist)

- [x] Identify product
- [x] Write this plan
- [ ] **Step 1** — Extract frames: run ffmpeg command above; verify count 200–260
- [ ] **Step 2** — Scaffold `index.html` with all 8 sections + loader/header/canvas/overlay/marquee/scroll-container
- [ ] **Step 3** — Write `css/style.css` (variables, side-align zones, hero standalone, mobile <768px collapse to centered + 550vh)
- [ ] **Step 4** — Write `js/app.js`: Lenis init, frame preloader (10 fast + rest bg), canvas padded-cover renderer (IMAGE_SCALE 0.85, FRAME_SPEED 2.0), section animation switch, counter tweens, marquee scrub, dark-overlay scrub, circle-wipe hero
- [ ] **Step 5** — Drop in copy (heritage, Bioceramic, SISTEM51, 8 shades, CTA)
- [ ] **Step 6** — Serve via `npx serve .` on port 3000; verify each section has a **distinct** animation type, no consecutive repeats
- [ ] **Step 7** — Mobile check at 375px; CTA persists at end

## Copy Bank (drafted, ready to drop in)

**Hero**
- Label: `2026 · Audemars Piguet × Swatch`
- Heading: `Royal Pop.`
- Tagline: `An icon, pocketed. Eight shades of Bioceramic. One movement, fifty-one parts.`

**001 — Heritage**
> Two icons converge. The octagonal silhouette of the 1972 Royal Oak meets the playful loop of the 1980s Swatch POP. Worn on a chain, a belt loop, a lanyard — never on the wrist.

**002 — Bioceramic**
> Two-thirds ceramic powder. One-third bio-sourced material from castor oil. The result is a case that feels lighter than it looks and harder than it feels.

**003 — SISTEM51**
> Swatch's SISTEM51 movement, reimagined as a hand-wound caliber. Fifty-one components. Fifteen active patents. Assembled in a single automated step. No wrist required.

**Stats**
- `8` models · Cold colors and warm
- `51` components · One movement, fully automated
- `15` active patents · SISTEM51 hand-wound
- `1972` Royal Oak origin year

**004 — Silhouettes**
> **Lépine** — winding crown at 12. Six models. The clean read.
> **Savonnette** — crown at 3, small seconds at 6. Two models. The technical read.

**005 — Eight Shades**
> LAN BA · BLAUE ACHT · OCHO NEGRO · and five more. From cold monochrome to tutti-frutti.

**CTA**
- Headline: `Find your shade.`
- Body: `Available at selected Swatch boutiques. One per person, per store, per day.`
- Button: `Locate a boutique →` (links to swatch.com/en-us/royal-pop.html)
- Price tag: `From $400 USD · Lépine · $420 USD · Savonnette`

## Status

**Current step:** ready to start Step 1 (frame extraction). All planning + content drafting complete. If restarting: jump to the **Build Steps** checklist and run the next unchecked item.
