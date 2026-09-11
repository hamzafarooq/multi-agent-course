import { useEffect, useRef } from "react";

/**
 * The six spec documents as a fanned stack that leans toward the pointer.
 * Pointer position drives a 3D tilt on the scene and a per-card parallax by
 * depth; motion is eased with a small lerp and disabled under reduced motion.
 */
const DOCS = [
  { file: "scope.md", line: "Level, core loop, excludes", depth: 0 },
  { file: "reference-brief.md", line: "What the reference does", depth: 1 },
  { file: "prd.md", line: "Goals, non-goals, stories", depth: 2 },
  { file: "decisions.md", line: "Scope cuts vs. reference", depth: 3 },
  { file: "user-stories.md", line: "Given / When / Then", depth: 4 },
  { file: "api-contract.md", line: "The one file both engineers build from", depth: 5, law: true },
];

export function HeroObject() {
  const sceneRef = useRef<HTMLDivElement>(null);
  const target = useRef({ x: 0, y: 0 });
  const current = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;

    const onMove = (e: PointerEvent) => {
      const r = scene.getBoundingClientRect();
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      // Normalised -1..1 from the scene's centre, clamped so far-away pointers still steer gently.
      target.current = {
        x: Math.max(-1, Math.min(1, (e.clientX - cx) / (r.width * 0.9))),
        y: Math.max(-1, Math.min(1, (e.clientY - cy) / (r.height * 0.9))),
      };
    };
    const onLeave = () => {
      target.current = { x: 0, y: 0 };
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave);
    document.addEventListener("mouseleave", onLeave);

    let raf = 0;
    const cards = Array.from(scene.querySelectorAll<HTMLElement>("[data-depth]"));
    const glow = scene.querySelector<HTMLElement>("[data-glow]");
    const tick = () => {
      current.current.x += (target.current.x - current.current.x) * 0.08;
      current.current.y += (target.current.y - current.current.y) * 0.08;
      const { x, y } = current.current;
      scene.style.transform = `rotateX(${(-y * 9).toFixed(2)}deg) rotateY(${(x * 12).toFixed(2)}deg)`;
      for (const c of cards) {
        const d = Number(c.dataset.depth);
        const k = 4 + d * 3.5;
        c.style.transform = `translate3d(${(x * k).toFixed(2)}px, ${(y * k).toFixed(2)}px, ${d * 18}px)`;
      }
      if (glow) glow.style.transform = `translate3d(${(x * 60).toFixed(1)}px, ${(y * 60).toFixed(1)}px, 0)`;
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
      document.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return (
    <div className="relative h-[420px] w-full select-none" style={{ perspective: "1200px" }} aria-hidden>
      <div
        data-glow
        className="absolute left-1/2 top-1/2 h-[320px] w-[320px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-surface-3 blur-3xl opacity-70 will-change-transform"
      />
      <div ref={sceneRef} className="relative h-full w-full will-change-transform" style={{ transformStyle: "preserve-3d" }}>
        {DOCS.map((d, i) => {
          const n = DOCS.length - 1;
          const spread = (i - n / 2) * 14;
          const rot = (i - n / 2) * 2.2;
          return (
            <div
              key={d.file}
              data-depth={d.depth}
              className={
                "absolute left-1/2 top-1/2 w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-surface will-change-transform " +
                (d.law ? "border-fg shadow-[var(--shadow-elev-2)]" : "border-border shadow-[var(--shadow-elev-1)]")
              }
              style={{
                marginLeft: `${spread * 2.2}px`,
                marginTop: `${-spread * 1.1}px`,
                rotate: `${rot}deg`,
                zIndex: i,
              }}
            >
              <div className="px-4 pt-3 pb-3.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[12px] text-fg">{d.file}</span>
                  <span className="font-mono text-[10.5px] text-fg-subtle">{String(i + 1).padStart(2, "0")}</span>
                </div>
                <div className="mt-1.5 text-[12.5px] text-fg-muted leading-snug">{d.line}</div>
                {d.law ? (
                  <div className="mt-3 inline-flex items-center rounded-full bg-fg px-2 py-0.5 text-[10.5px] font-medium uppercase tracking-wide text-bg">
                    the contract is law
                  </div>
                ) : (
                  <div className="mt-3 space-y-1.5">
                    <div className="h-1.5 w-[86%] rounded bg-surface-3" />
                    <div className="h-1.5 w-[64%] rounded bg-surface-3" />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
