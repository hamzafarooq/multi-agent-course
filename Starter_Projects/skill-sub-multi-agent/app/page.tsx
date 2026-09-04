'use client';

import { useMemo, useState } from 'react';
import { LEVELS } from '@/lib/demo-data';
import LevelSelector from '@/components/LevelSelector';
import SimulationView from '@/components/SimulationView';
import ConceptCallout from '@/components/ConceptCallout';

function Stepper({ levelId }: { levelId: number }) {
  const total = LEVELS.length;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingTop: 6 }} aria-label="level progress">
      {LEVELS.map((l) => (
        <div key={l.id} style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{
            width: 30, height: 30, borderRadius: '50%',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            border: `1px solid ${l.id === levelId ? 'var(--ink)' : 'var(--rule)'}`,
            background: l.id === levelId ? 'var(--ink)' : l.id < levelId ? 'var(--plate)' : 'var(--surface)',
            color: l.id === levelId ? 'var(--surface)' : l.id < levelId ? 'var(--ink-2)' : 'var(--ink-3)',
            fontSize: 10.5,
            fontFamily: 'inherit',
            transition: 'all 200ms ease',
          }}>
            {String(l.id).padStart(2, '0')}
          </div>
          {l.id < total && <div style={{ width: 18, height: 1, background: 'var(--rule)' }} />}
        </div>
      ))}
    </div>
  );
}

export default function Home() {
  const [activeId, setActiveId] = useState(1);
  const level = useMemo(() => LEVELS.find((l) => l.id === activeId)!, [activeId]);

  const COURSE_IMG = 'https://d2426xcxuh3ht5.cloudfront.net/ikyBoEMMRkODhnVnux3P_Duo%20Instructor%20-%20theme%20a.png';

  return (
    <div style={{ position: 'relative', zIndex: 2, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top bar */}
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 36px', borderBottom: '1px solid var(--rule)', background: 'var(--surface)' }}>
        <div style={{ width: '100%', maxWidth: 1180, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, whiteSpace: 'nowrap' }}>
            {/* Brand mark */}
            <span style={{ display: 'inline-flex', alignSelf: 'center', color: 'var(--ink)' }}>
              <svg viewBox="0 0 24 24" width="22" height="22">
                <circle cx="6" cy="6" r="2.4" fill="currentColor" />
                <circle cx="18" cy="6" r="2.4" fill="currentColor" />
                <circle cx="12" cy="18" r="2.4" fill="currentColor" />
                <path d="M6 6 L12 18 L18 6" stroke="currentColor" strokeWidth="1.1" fill="none" />
              </svg>
            </span>
            <span style={{ fontSize: 24, letterSpacing: '-0.01em', lineHeight: 1 }}>
              Agent Architectures
            </span>
          </div>

          {/* Meta */}
          <div style={{ display: 'flex', gap: 28 }}>
            {[{ label: 'mode', value: 'simulation' }, { label: 'api calls', value: '0' }].map(({ label, value }) => (
              <div key={label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
                <span style={{ fontSize: 9.5, textTransform: 'uppercase', letterSpacing: '0.16em', color: 'var(--ink-3)' }}>{label}</span>
                <span style={{ fontSize: 11, color: 'var(--ink)' }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </header>

      {/* Shell */}
      <div style={{ width: '100%', maxWidth: 1180, margin: '0 auto', display: 'grid', gridTemplateColumns: '248px 1fr', flex: 1, minHeight: 0, borderLeft: '1px solid var(--rule)', borderRight: '1px solid var(--rule)' }}>
        <LevelSelector levels={LEVELS} activeId={activeId} onSelect={setActiveId} />

        <main style={{ padding: '30px 36px 56px', display: 'flex', flexDirection: 'column', gap: 22, minWidth: 0 }}>
          {/* Level head */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 32 }}>
            <div style={{ maxWidth: 560 }}>
              <div style={{ fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 8 }}>
                Level {String(level.id).padStart(2, '0')} · <span style={{ color: 'var(--accent)' }}>{level.tagline}</span>
              </div>
              <h1 style={{ fontSize: 42, lineHeight: 1, letterSpacing: '-0.015em', margin: '0 0 10px', fontWeight: 400 }}>
                {level.name}
              </h1>
              <p style={{ margin: 0, fontSize: 14.5, color: 'var(--ink-2)', lineHeight: 1.55, maxWidth: '52ch' }}>
                {level.description}
              </p>
            </div>
            <Stepper levelId={level.id} />
          </div>

          <SimulationView key={activeId} level={level} />
          <ConceptCallout level={level} />
        </main>
      </div>

      {/* CTA — subtle corner link */}
      <a
        href="https://maven.com/boring-bot/advanced-llm"
        target="_blank"
        rel="noopener noreferrer"
        style={{
          position: 'fixed', bottom: 20, right: 24, zIndex: 40,
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'var(--surface)',
          border: '1px solid var(--rule)',
          borderRadius: 4,
          padding: '7px 12px',
          textDecoration: 'none',
          color: 'var(--ink-3)',
          fontSize: 11.5,
          letterSpacing: '0.01em',
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
          transition: 'color 120ms ease, border-color 120ms ease',
        }}
        onMouseEnter={(e) => {
          const el = e.currentTarget as HTMLAnchorElement;
          el.style.color = 'var(--ink)';
          el.style.borderColor = 'var(--ink-2)';
        }}
        onMouseLeave={(e) => {
          const el = e.currentTarget as HTMLAnchorElement;
          el.style.color = 'var(--ink-3)';
          el.style.borderColor = 'var(--rule)';
        }}
      >
        <img
          src={COURSE_IMG}
          alt=""
          style={{ height: 20, width: 'auto', opacity: 0.85 }}
          onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
        />
        <span>Agent Engineering Bootcamp</span>
        <span style={{ fontSize: 10, opacity: 0.5 }}>→</span>
      </a>
    </div>
  );
}
