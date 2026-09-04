---
name: video-to-website
description: Use when someone asks to turn a video into a website, create a scroll-driven animated page from video frames, or build a premium scroll experience with canvas rendering.
user_invocable: true
disable-model-invocation: true
argument-hint: <video-file-path>
credit: https://lobehub.com/skills/remamare13-claude-framework-video-to-website
---

# Video to Premium Scroll-Driven Website

Turn a video file into a scroll-driven animated website with **animation variety and choreography** — multiple animation types working together, not one repeated effect.

## Input

The user provides: a video file path (MP4, MOV, etc.) and optionally:
- A theme/brand name
- Desired text sections and where they appear
- Color scheme preferences
- Any specific design direction

If the user doesn't specify these, ask briefly or use sensible creative defaults.

## Premium Checklist (Non-Negotiable)

1. **Lenis smooth scroll** — native scroll feels "web page," Lenis feels "experience"
2. **4+ animation types** — never repeat the same entrance animation consecutively
3. **Staggered reveals** — label → heading → body → CTA, never all at once
4. **No glassmorphism cards** — text on clean backgrounds, hierarchy via font size/weight/color
5. **Direction variety** — sections enter from different directions (left, right, up, scale, clip)
6. **Dark overlay for stats** — 0.88-0.92 opacity, counters animate up, only time center text is OK
7. **Horizontal text marquee** — at least one oversized text element sliding on scroll (12vw+)
8. **Counter animations** — all numbers count up from 0, never appear statically
9. **Massive typography** — hero 12rem+, section headings 4rem+, marquee 10vw+
10. **CTA persists** — `data-persist="true"` keeps final section visible, never disappears
11. **Hero prominence + generous scroll** — hero gets 20%+ scroll range, 800vh+ total for 6 sections
12. **Side-aligned text ONLY** — all text in outer 40% zones (`align-left`/`align-right`), never center. Exception: stats with full dark overlay
13. **Circle-wipe hero reveal** — hero is standalone 100vh section, canvas reveals via `clip-path: circle()` as hero scrolls away
14. **Frame speed 1.8-2.2** — product animation completes by ~55% scroll. Below 1.8 feels sluggish

## Workflow

**Prerequisites:** FFmpeg and FFprobe must be installed and available on PATH. Verify with `which ffmpeg` (Unix) or `where ffmpeg` (Windows) before proceeding.

### Step 1: Analyze the Video

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration,r_frame_rate,nb_frames -of csv=p=0 "<VIDEO_PATH>"
```

Determine resolution, duration, frame rate, total frames. Decide:
- **Target frame count**: 150-300 frames for good scroll experience
  - Short video (<10s): extract at original fps, cap at ~300
  - Medium (10-30s): extract at 10-15fps
  - Long (30s+): extract at 5-10fps
- **Output resolution**: Match aspect ratio, cap width at 1920px

### Step 2: Extract Frames

```bash
mkdir -p frames
ffmpeg -i "<VIDEO_PATH>" -vf "fps=<CALCULATED_FPS>,scale=<WIDTH>:-1" -c:v libwebp -quality 80 "frames/frame_%04d.webp"
```

After extraction, count frames: `ls frames/ | wc -l`

### Step 3: Scaffold

```
project-root/
  index.html
  css/style.css
  js/app.js
  frames/frame_0001.webp ...
```

No bundler. Vanilla HTML/CSS/JS + CDN libraries.

### Step 4: Build index.html

Required structure (in this order):

```html
<!-- 1. Loader: #loader > .loader-brand, #loader-bar, #loader-percent -->
<!-- 2. Fixed header: .site-header > nav with logo + links -->
<!-- 3. Hero: .hero-standalone (100vh, solid bg, word-split heading) -->
<!--    Contains: .section-label, .hero-heading (words in spans), .hero-tagline -->
<!--    Scroll indicator with arrow -->
<!-- 4. Canvas: .canvas-wrap > canvas#canvas (fixed, full viewport) -->
<!-- 5. Dark overlay: #dark-overlay (fixed, full viewport, pointer-events:none) -->
<!-- 6. Marquee(s): .marquee-wrap > .marquee-text (fixed, 12vw font) -->
<!-- 7. Scroll container: #scroll-container (800vh+) -->
<!--    Content sections with data-enter, data-leave, data-animation -->
<!--    Stats section with .stat-number[data-value][data-decimals] -->
<!--    CTA section with data-persist="true" -->
```

Content section example:
```html
<section class="scroll-section section-content align-left"
         data-enter="22" data-leave="38" data-animation="slide-left">
  <div class="section-inner">
    <span class="section-label">002 / Feature</span>
    <h2 class="section-heading">Feature Headline</h2>
    <p class="section-body">Description text here.</p>
  </div>
</section>
```

Stats section example:
```html
<section class="scroll-section section-stats"
         data-enter="54" data-leave="72" data-animation="stagger-up">
  <div class="stats-grid">
    <div class="stat">
      <span class="stat-number" data-value="24" data-decimals="0">0</span>
      <span class="stat-suffix">hrs</span>
      <span class="stat-label">Cold retention</span>
    </div>
  </div>
</section>
```

CDN scripts (end of body, this order):
```html
<script src="https://cdn.jsdelivr.net/npm/lenis@1/dist/lenis.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/ScrollTrigger.min.js"></script>
<script src="js/app.js"></script>
```

### Step 5: Build css/style.css

Use the **frontend-design** skill for creative, distinctive styling. Key technical patterns:

```css
:root {
  --bg-light: #f5f3f0;
  --bg-dark: #111111;
  --text-on-light: #1a1a1a;
  --text-on-dark: #f0ede8;
  --font-display: '[DISPLAY FONT]', sans-serif;
  --font-body: '[BODY FONT]', sans-serif;
}

/* Side-aligned text zones — product occupies center */
.align-left { padding-left: 5vw; padding-right: 55vw; }
.align-right { padding-left: 55vw; padding-right: 5vw; }
.align-left .section-inner,
.align-right .section-inner { max-width: 40vw; }
```

- **Hero-first layout**: Hero is standalone 100vh with solid bg. Canvas starts hidden, reveals via circle-wipe as hero scrolls away.
- **Scroll sections**: `position: absolute` within scroll container, positioned at midpoint of enter/leave range, `transform: translateY(-50%)`.
- **Mobile (<768px)**: Collapse side alignment to centered text with dark backdrop overlays. Reduce scroll height to ~550vh.
- **Text contrast**: Never use `#999` for important text on light backgrounds. Use `#666` minimum for body, `var(--text-on-light)` for headings.

### Step 6: Build js/app.js

#### 6a. Lenis Smooth Scroll (MANDATORY)

```js
const lenis = new Lenis({
  duration: 1.2,
  easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  smoothWheel: true
});
lenis.on("scroll", ScrollTrigger.update);
gsap.ticker.add((time) => lenis.raf(time * 1000));
gsap.ticker.lagSmoothing(0);
```

#### 6b. Frame Preloader

Two-phase loading: load first 10 frames immediately (fast first paint), then load remaining frames in background. Show progress bar during load. Hide loader only after all frames are ready.

#### 6c. Canvas Renderer — Padded Cover Mode

```js
const IMAGE_SCALE = 0.85; // 0.82-0.90 sweet spot
function drawFrame(index) {
  const img = frames[index];
  if (!img) return;
  const cw = canvas.width, ch = canvas.height;
  const iw = img.naturalWidth, ih = img.naturalHeight;
  const scale = Math.max(cw / iw, ch / ih) * IMAGE_SCALE;
  const dw = iw * scale, dh = ih * scale;
  const dx = (cw - dw) / 2, dy = (ch - dh) / 2;
  ctx.fillStyle = bgColor; // sampled from frame corners
  ctx.fillRect(0, 0, cw, ch);
  ctx.drawImage(img, dx, dy, dw, dh);
}
```

- Auto-sample background color from frame edge pixels with `sampleBgColor()` every ~20 frames
- Fill canvas with sampled color BEFORE drawing (fills the thin padded border seamlessly)
- Apply devicePixelRatio scaling for crisp rendering
- Optional: edge feathering gradients for smoother blend

#### 6d. Frame-to-Scroll Binding

```js
const FRAME_SPEED = 2.0; // 1.8-2.2, higher = product animation finishes earlier
ScrollTrigger.create({
  trigger: scrollContainer,
  start: "top top",
  end: "bottom bottom",
  scrub: true,
  onUpdate: (self) => {
    const accelerated = Math.min(self.progress * FRAME_SPEED, 1);
    const index = Math.min(Math.floor(accelerated * FRAME_COUNT), FRAME_COUNT - 1);
    if (index !== currentFrame) {
      currentFrame = index;
      requestAnimationFrame(() => drawFrame(currentFrame));
    }
  }
});
```

#### 6e. Section Animation System

Each section reads `data-animation` and gets a different entrance. Sections with `data-persist="true"` stay visible once animated in. Position sections absolutely at the midpoint of their enter/leave range with `translateY(-50%)`.

```js
function setupSectionAnimation(section) {
  const type = section.dataset.animation;
  const persist = section.dataset.persist === "true";
  const enter = parseFloat(section.dataset.enter) / 100;
  const leave = parseFloat(section.dataset.leave) / 100;
  const children = section.querySelectorAll(
    ".section-label, .section-heading, .section-body, .section-note, .cta-button, .stat"
  );

  const tl = gsap.timeline({ paused: true });

  switch (type) {
    case "fade-up":
      tl.from(children, { y: 50, opacity: 0, stagger: 0.12, duration: 0.9, ease: "power3.out" });
      break;
    case "slide-left":
      tl.from(children, { x: -80, opacity: 0, stagger: 0.14, duration: 0.9, ease: "power3.out" });
      break;
    case "slide-right":
      tl.from(children, { x: 80, opacity: 0, stagger: 0.14, duration: 0.9, ease: "power3.out" });
      break;
    case "scale-up":
      tl.from(children, { scale: 0.85, opacity: 0, stagger: 0.12, duration: 1.0, ease: "power2.out" });
      break;
    case "rotate-in":
      tl.from(children, { y: 40, rotation: 3, opacity: 0, stagger: 0.1, duration: 0.9, ease: "power3.out" });
      break;
    case "stagger-up":
      tl.from(children, { y: 60, opacity: 0, stagger: 0.15, duration: 0.8, ease: "power3.out" });
      break;
    case "clip-reveal":
      tl.from(children, { clipPath: "inset(100% 0 0 0)", opacity: 0, stagger: 0.15, duration: 1.2, ease: "power4.inOut" });
      break;
  }

  // Play/reverse based on scroll position via ScrollTrigger onUpdate
  // If persist is true, never reverse when scrolling past the leave point
}
```

#### 6f. Counter Animations

```js
document.querySelectorAll(".stat-number").forEach(el => {
  const target = parseFloat(el.dataset.value);
  const decimals = parseInt(el.dataset.decimals || "0");
  gsap.from(el, {
    textContent: 0,
    duration: 2,
    ease: "power1.out",
    snap: { textContent: decimals === 0 ? 1 : 0.01 },
    scrollTrigger: { trigger: el.closest(".scroll-section"), start: "top 70%", toggleActions: "play none none reverse" }
  });
});
```

#### 6g. Horizontal Text Marquee

```js
document.querySelectorAll(".marquee-wrap").forEach(el => {
  const speed = parseFloat(el.dataset.scrollSpeed) || -25;
  gsap.to(el.querySelector(".marquee-text"), {
    xPercent: speed,
    ease: "none",
    scrollTrigger: { trigger: scrollContainer, start: "top top", end: "bottom bottom", scrub: true }
  });
  // Fade marquee in/out based on scroll range using opacity transitions
});
```

#### 6h. Dark Overlay

```js
function initDarkOverlay(enter, leave) {
  const overlay = document.getElementById("dark-overlay");
  const fadeRange = 0.04;
  ScrollTrigger.create({
    trigger: scrollContainer,
    start: "top top",
    end: "bottom bottom",
    scrub: true,
    onUpdate: (self) => {
      const p = self.progress;
      let opacity = 0;
      if (p >= enter - fadeRange && p <= enter) opacity = (p - (enter - fadeRange)) / fadeRange;
      else if (p > enter && p < leave) opacity = 0.9;
      else if (p >= leave && p <= leave + fadeRange) opacity = 0.9 * (1 - (p - leave) / fadeRange);
      overlay.style.opacity = opacity;
    }
  });
}
```

#### 6i. Circle-Wipe Hero Reveal

```js
function initHeroTransition() {
  ScrollTrigger.create({
    trigger: scrollContainer,
    start: "top top",
    end: "bottom bottom",
    scrub: true,
    onUpdate: (self) => {
      const p = self.progress;
      // Hero fades out as scroll begins
      heroSection.style.opacity = Math.max(0, 1 - p * 15);
      // Canvas reveals via expanding circle clip-path
      const wipeProgress = Math.min(1, Math.max(0, (p - 0.01) / 0.06));
      const radius = wipeProgress * 75; // 0% to 75% of viewport
      canvasWrap.style.clipPath = `circle(${radius}% at 50% 50%)`;
    }
  });
}
```

### Step 7: Test

1. Serve locally: `npx serve .` or `python -m http.server 8000`
2. Scroll through fully — verify each section has a DIFFERENT animation type
3. Confirm: smooth scroll, frame playback, staggered reveals, marquee slides, counters count up, dark overlay fades, CTA persists at end

## Animation Types Quick Reference

| Type | Initial State | Animate To | Duration |
|------|--------------|-----------|----------|
| `fade-up` | y:50, opacity:0 | y:0, opacity:1 | 0.9s |
| `slide-left` | x:-80, opacity:0 | x:0, opacity:1 | 0.9s |
| `slide-right` | x:80, opacity:0 | x:0, opacity:1 | 0.9s |
| `scale-up` | scale:0.85, opacity:0 | scale:1, opacity:1 | 1.0s |
| `rotate-in` | y:40, rotation:3, opacity:0 | y:0, rotation:0, opacity:1 | 0.9s |
| `stagger-up` | y:60, opacity:0 | y:0, opacity:1 | 0.8s |
| `clip-reveal` | clipPath:inset(100% 0 0 0) | clipPath:inset(0% 0 0 0) | 1.2s |

All types use stagger (0.1-0.15s) and ease `power3.out` (except scale-up: `power2.out`, clip-reveal: `power4.inOut`).

## Anti-Patterns

- **Cycling feature cards in a pinned section** — each card gets too little scroll time. Give each feature its own scroll-triggered section (8-10% range) with its own animation type
- **Pure cover mode** (`Math.max` at 1.0) — product clips into header. Use `IMAGE_SCALE` 0.82-0.90
- **Pure contain mode** (`Math.min`) — leaves visible border that doesn't match page bg
- **FRAME_SPEED < 1.8** — product animation feels sluggish, use 1.8-2.2
- **Hero < 20% scroll range** — first impression needs breathing room
- **Same animation for consecutive sections** — never repeat the same entrance type back-to-back
- **Wide centered grids over canvas** — redesign as vertical lists in the 40% side zone
- **Scroll height < 800vh** for 6 sections — everything feels rushed

## Clip-Path Variations

- Circle reveal: `circle(0% at 50% 50%)` → `circle(75% at 50% 50%)`
- Wipe from left: `inset(0 100% 0 0)` → `inset(0 0% 0 0)`
- Wipe from bottom: `inset(100% 0 0 0)` → `inset(0% 0 0 0)`
- Custom polygon: `polygon(50% 0%, 50% 0%, 50% 100%, 50% 100%)` → `polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)`

## Troubleshooting

- **Frames not loading**: Must serve via HTTP, not `file://`
- **Choppy scrolling**: Increase `scrub` value, reduce frame count
- **White flashes**: Ensure all frames loaded before hiding loader
- **Blurry canvas**: Apply `devicePixelRatio` scaling to canvas dimensions
- **Lenis conflicts**: Ensure `lenis.on("scroll", ScrollTrigger.update)` is connected
- **Counters not animating**: Verify `data-value` attribute exists and snap settings match decimal places
- **Memory issues on mobile**: Reduce frames to <150, resize to 1280px wide
- **FFmpeg not found**: Install via `brew install ffmpeg` (macOS), `apt install ffmpeg` (Linux), or download from ffmpeg.org (Windows)
