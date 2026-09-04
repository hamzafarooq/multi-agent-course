# Next Session — Royal Pop Landing Page

> Resumable handoff. Read this file first if returning to the project.

## Current state (as of last session)

**Live and working.** Site served at `http://localhost:8787` (Python http.server in the `vantage` conda env, background id `behh6mgac` if still running).

### What's built
- 241 JPEG frames extracted from `video/8887ad431858cde1fcfde38c3d45edcd_1779083229_lslzo3i4.mp4` (15s, 1280×720, 16fps)
- `index.html` — loader, fixed header, hero (100vh standalone), canvas wrap, dark overlay, marquee, 7 scroll sections inside a 900vh container
- `css/style.css` — Fraunces + Inter, cream `#f5f3f0` palette, directional vignettes for text readability, mobile breakpoint at 768px
- `js/app.js` — Lenis smooth scroll, two-phase frame preloader, padded-cover canvas renderer, GSAP timelines per section, counters, marquee scrub, circle-wipe hero, dynamic body bg sampled from canvas frames

### Issues fixed in this session
1. `position:absolute; top:50%` made sections invisible during scroll → switched to `position:fixed` opacity-driven
2. Dark text unreadable over colourful frames → light cream text + directional dark vignette per side
3. CTA "Available now." had dark text → added radial vignette + light text
4. Marquee invisible over dark frames → `mix-blend-mode: difference` with white text
5. Page bg edge didn't match canvas → `drawFrame()` writes sampled bgColor to `document.body.style.backgroundColor` every 20 frames
6. CTA button overlapping price note → converted `.cta-inner` to `display: flex; flex-direction: column; gap: 24px` (then user asked to remove the price line entirely)

## Known good defaults

| Knob | Value | Where |
|---|---|---|
| Frame count | 241 | `js/app.js` `FRAME_COUNT` |
| Frame speed | 2.0 | `js/app.js` `FRAME_SPEED` |
| Image scale (padding) | 0.85 | `js/app.js` `IMAGE_SCALE` |
| Scroll container height | 900vh (desktop), 600vh (mobile) | `css/style.css` |
| Hero scroll range | 0–8% | implicit (first section enters at 8%) |
| Section enter/leave windows | see `index.html` `data-enter`/`data-leave` | per `<section>` |

## If picking up cold — quickstart

```bash
# 1. Activate env
conda activate vantage

# 2. Serve
cd "/Users/traversaal-001-hf/Dropbox/Mac (3)/Documents/Github/royal-pop-website"
python -m http.server 8787

# 3. Open
open http://localhost:8787
```

If frames are missing (gitignored on remote clones), re-extract:

```bash
mkdir -p frames
ffmpeg -y -i "video/8887ad431858cde1fcfde38c3d45edcd_1779083229_lslzo3i4.mp4" \
  -vf "fps=16,scale=1280:-1" -q:v 4 "frames/frame_%04d.jpg"
ls frames | wc -l   # should print 241
```

## Possible next moves

- **Reshoot video** with white/cream `#f5f3f0` background per `README.md` Step 0. Then revert the dark vignettes (they only exist because the current video has a dark green backdrop).
- **Match navigation jump-links** to actual section IDs — the `#heritage`, `#bioceramic`, `#movement`, `#shades` anchors exist but a Lenis scrollTo handler isn't wired up. Currently the browser does a hard native jump which Lenis doesn't smooth.
- **Add a 6th content section** — Care / Provenance / Maintenance — between Shades and CTA, with a `fade-up` animation. Update enter/leave windows accordingly (compress others by ~5% each).
- **Replace JPEG frames with WebP** if you install an ffmpeg build with `libwebp` (`brew reinstall ffmpeg --with-libwebp` is gone now; use a static build from evermeet.cx or compile yourself). ~40% smaller for the same quality.
- **Mobile polish** — current breakpoint flattens to centered text with backdrop. Verify on a real device; iOS Safari sometimes pinches Lenis-scrolled pages.
- **Lighthouse pass** — preload key frames, defer GSAP, add proper `<meta>` tags for social sharing.

## Push plan (decided)

User chose: **subfolder in claude-code-starter, frames gitignored.**

Steps the next session should run:

1. Create `.gitignore` in this folder with:
   ```
   frames/
   video/
   .DS_Store
   ```
2. Verify nothing sensitive in the working tree (`git status` from parent)
3. Clone `https://github.com/hamzafarooq/claude-code-starter` to a sibling directory
4. Copy this folder into the clone as `examples/royal-pop-website/` (skip `frames/` and `video/`)
5. Add a short pointer in the root README of claude-code-starter linking to the example
6. Commit with message like "Add Royal Pop scroll-driven landing page example"
7. Push to `main` (or open a PR)

The user's video file is large (~3MB) and is referenced by the extraction command — decide whether to commit the video itself (probably yes, so frames are reproducible) or gitignore it too (cloners must supply their own).
