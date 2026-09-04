/* =====================================================
   Royal Pop — scroll choreography
   ===================================================== */

gsap.registerPlugin(ScrollTrigger);

const FRAME_COUNT = 241;
const FRAME_PATH = (i) => `frames/frame_${String(i + 1).padStart(4, "0")}.jpg`;
const FRAME_SPEED = 2.0;
const IMAGE_SCALE = 0.85;

const frames = new Array(FRAME_COUNT);
let bgColor = "#f5f3f0";
let currentFrame = -1;
let scrollContainer, canvas, ctx, canvasWrap, heroSection;

/* -----------------------------------------------------
   Lenis smooth scroll
   ----------------------------------------------------- */
const lenis = new Lenis({
  duration: 1.2,
  easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  smoothWheel: true,
});
lenis.on("scroll", ScrollTrigger.update);
gsap.ticker.add((time) => lenis.raf(time * 1000));
gsap.ticker.lagSmoothing(0);

/* -----------------------------------------------------
   Boot
   ----------------------------------------------------- */
document.addEventListener("DOMContentLoaded", init);

function init() {
  scrollContainer = document.getElementById("scroll-container");
  canvas = document.getElementById("canvas");
  ctx = canvas.getContext("2d");
  canvasWrap = document.querySelector(".canvas-wrap");
  heroSection = document.querySelector(".hero-standalone");

  sizeCanvas();
  window.addEventListener("resize", () => {
    sizeCanvas();
    drawFrame(currentFrame >= 0 ? currentFrame : 0);
  });

  preloadFrames().then(() => {
    hideLoader();
    drawFrame(0);
    initFrameBinding();
    initHeroTransition();
    initMarquees();
    initDarkOverlayForStats();
    initSections();
    initCounters();
    ScrollTrigger.refresh();
  });
}

/* -----------------------------------------------------
   Canvas sizing
   ----------------------------------------------------- */
function sizeCanvas() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = window.innerWidth * dpr;
  canvas.height = window.innerHeight * dpr;
  canvas.style.width = window.innerWidth + "px";
  canvas.style.height = window.innerHeight + "px";
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

/* -----------------------------------------------------
   Frame preloader (two-phase)
   ----------------------------------------------------- */
function preloadFrames() {
  const loaderBar = document.getElementById("loader-bar-fill");
  const loaderPct = document.getElementById("loader-percent");
  let loaded = 0;

  const loadOne = (i) =>
    new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        frames[i] = img;
        loaded++;
        const pct = Math.round((loaded / FRAME_COUNT) * 100);
        loaderBar.style.width = pct + "%";
        loaderPct.textContent = pct + "%";
        if (i === 0) bgColor = sampleBgColor(img);
        resolve();
      };
      img.onerror = () => { loaded++; resolve(); };
      img.src = FRAME_PATH(i);
    });

  const firstBatch = [];
  for (let i = 0; i < Math.min(10, FRAME_COUNT); i++) firstBatch.push(loadOne(i));

  return Promise.all(firstBatch).then(() => {
    const rest = [];
    for (let i = 10; i < FRAME_COUNT; i++) rest.push(loadOne(i));
    return Promise.all(rest);
  });
}

function sampleBgColor(img) {
  try {
    const c = document.createElement("canvas");
    c.width = 16; c.height = 16;
    const cx = c.getContext("2d");
    cx.drawImage(img, 0, 0, 16, 16);
    const d = cx.getImageData(0, 0, 16, 16).data;
    let r = 0, g = 0, b = 0, n = 0;
    const sample = (x, y) => {
      const idx = (y * 16 + x) * 4;
      r += d[idx]; g += d[idx + 1]; b += d[idx + 2]; n++;
    };
    for (let x = 0; x < 16; x++) { sample(x, 0); sample(x, 15); }
    for (let y = 1; y < 15; y++) { sample(0, y); sample(15, y); }
    r = Math.round(r / n); g = Math.round(g / n); b = Math.round(b / n);
    return `rgb(${r}, ${g}, ${b})`;
  } catch (e) {
    return "#f5f3f0";
  }
}

function hideLoader() {
  document.getElementById("loader").classList.add("hidden");
}

/* -----------------------------------------------------
   Canvas renderer — padded cover
   ----------------------------------------------------- */
function drawFrame(index) {
  const img = frames[index];
  if (!img) return;
  const cw = canvas.width, ch = canvas.height;
  const iw = img.naturalWidth, ih = img.naturalHeight;
  const scale = Math.max(cw / iw, ch / ih) * IMAGE_SCALE;
  const dw = iw * scale, dh = ih * scale;
  const dx = (cw - dw) / 2, dy = (ch - dh) / 2;
  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, cw, ch);
  ctx.drawImage(img, dx, dy, dw, dh);

  if (index % 20 === 0) {
    bgColor = sampleBgColor(img);
    document.body.style.backgroundColor = bgColor;
  }
}

/* -----------------------------------------------------
   Frame → scroll
   ----------------------------------------------------- */
function initFrameBinding() {
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
    },
  });
}

/* -----------------------------------------------------
   Circle-wipe hero reveal
   ----------------------------------------------------- */
function initHeroTransition() {
  ScrollTrigger.create({
    trigger: scrollContainer,
    start: "top top",
    end: "bottom bottom",
    scrub: true,
    onUpdate: (self) => {
      const p = self.progress;
      heroSection.style.opacity = Math.max(0, 1 - p * 15);
      heroSection.style.pointerEvents = p > 0.05 ? "none" : "auto";
      const wipeProgress = Math.min(1, Math.max(0, (p - 0.01) / 0.06));
      const radius = wipeProgress * 90;
      canvasWrap.style.clipPath = `circle(${radius}% at 50% 50%)`;
    },
  });
}

/* -----------------------------------------------------
   Marquee
   ----------------------------------------------------- */
function initMarquees() {
  document.querySelectorAll(".marquee-wrap").forEach((el) => {
    const speed = parseFloat(el.dataset.scrollSpeed) || -25;
    const enter = parseFloat(el.dataset.enter) / 100;
    const leave = parseFloat(el.dataset.leave) / 100;

    gsap.to(el.querySelector(".marquee-text"), {
      xPercent: speed,
      ease: "none",
      scrollTrigger: {
        trigger: scrollContainer,
        start: "top top",
        end: "bottom bottom",
        scrub: true,
      },
    });

    ScrollTrigger.create({
      trigger: scrollContainer,
      start: "top top",
      end: "bottom bottom",
      scrub: true,
      onUpdate: (self) => {
        const p = self.progress;
        const fade = 0.04;
        let opacity = 0;
        if (p >= enter - fade && p <= enter) opacity = (p - (enter - fade)) / fade;
        else if (p > enter && p < leave) opacity = 1;
        else if (p >= leave && p <= leave + fade) opacity = 1 - (p - leave) / fade;
        el.style.opacity = opacity;
      },
    });
  });
}

/* -----------------------------------------------------
   Dark overlay (driven by stats section)
   ----------------------------------------------------- */
function initDarkOverlayForStats() {
  const stats = document.querySelector(".section-stats");
  if (!stats) return;
  const enter = parseFloat(stats.dataset.enter) / 100;
  const leave = parseFloat(stats.dataset.leave) / 100;
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
      if (p >= enter - fadeRange && p <= enter) opacity = 0.9 * ((p - (enter - fadeRange)) / fadeRange);
      else if (p > enter && p < leave) opacity = 0.9;
      else if (p >= leave && p <= leave + fadeRange) opacity = 0.9 * (1 - (p - leave) / fadeRange);
      overlay.style.opacity = opacity;
    },
  });
}

/* -----------------------------------------------------
   Section reveal animations
   ----------------------------------------------------- */
function initSections() {
  document.querySelectorAll(".scroll-section").forEach((section) => {
    setupSectionAnimation(section);
  });
}

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
      tl.from(children, {
        clipPath: "inset(100% 0 0 0)",
        opacity: 0,
        stagger: 0.15,
        duration: 1.2,
        ease: "power4.inOut",
      });
      break;
    default:
      tl.from(children, { y: 40, opacity: 0, stagger: 0.12, duration: 0.9, ease: "power3.out" });
  }

  const animateInPoint = enter + 0.02;
  const animateOutPoint = leave - 0.01;
  let played = false;

  ScrollTrigger.create({
    trigger: scrollContainer,
    start: "top top",
    end: "bottom bottom",
    scrub: true,
    onUpdate: (self) => {
      const p = self.progress;

      // Visibility window
      const fade = 0.03;
      let opacity = 0;
      if (p >= enter - fade && p <= enter) opacity = (p - (enter - fade)) / fade;
      else if (p > enter && p < leave) opacity = 1;
      else if (persist && p >= leave) opacity = 1;
      else if (p >= leave && p <= leave + fade) opacity = 1 - (p - leave) / fade;
      section.style.opacity = opacity;

      // Trigger entrance once visible
      if (p >= animateInPoint && !played) {
        tl.play();
        played = true;
      }
      if (!persist && p < enter - fade && played) {
        tl.reverse();
        played = false;
      }
    },
  });
}

/* -----------------------------------------------------
   Counters
   ----------------------------------------------------- */
function initCounters() {
  document.querySelectorAll(".stat-number").forEach((el) => {
    const target = parseFloat(el.dataset.value);
    const decimals = parseInt(el.dataset.decimals || "0", 10);
    const section = el.closest(".scroll-section");
    const enter = parseFloat(section.dataset.enter) / 100;
    let played = false;

    ScrollTrigger.create({
      trigger: scrollContainer,
      start: "top top",
      end: "bottom bottom",
      scrub: true,
      onUpdate: (self) => {
        if (self.progress >= enter + 0.01 && !played) {
          played = true;
          const obj = { val: 0 };
          gsap.to(obj, {
            val: target,
            duration: 2,
            ease: "power1.out",
            onUpdate: () => {
              el.textContent = decimals === 0
                ? Math.round(obj.val).toString()
                : obj.val.toFixed(decimals);
            },
          });
        }
      },
    });
  });
}
