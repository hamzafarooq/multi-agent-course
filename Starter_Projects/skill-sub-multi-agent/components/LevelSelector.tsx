'use client';

import { LevelDef } from '@/lib/demo-data';
import FileTree from './FileTree';

interface Props {
  levels: LevelDef[];
  activeId: number;
  onSelect: (id: number) => void;
}

export default function LevelSelector({ levels, activeId, onSelect }: Props) {
  return (
    <aside style={{ borderRight: '1px solid var(--rule)', padding: '26px 18px 22px', display: 'flex', flexDirection: 'column', gap: 28, background: 'var(--surface)', width: 248, flexShrink: 0 }}>
      <div>
        <div style={{ fontFamily: 'inherit', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 12 }}>
          Levels
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {levels.map((lvl) => {
            const active = lvl.id === activeId;
            return (
              <button
                key={lvl.id}
                onClick={() => onSelect(lvl.id)}
                aria-pressed={active}
                style={{
                  appearance: 'none',
                  background: active ? 'var(--ink)' : 'transparent',
                  border: `1px solid ${active ? 'var(--ink)' : 'transparent'}`,
                  borderRadius: 4,
                  padding: '10px 12px 12px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  color: active ? 'var(--surface)' : 'var(--ink)',
                  transition: 'background 120ms ease, border-color 120ms ease',
                }}
                onMouseEnter={(e) => { if (!active) (e.currentTarget as HTMLButtonElement).style.background = 'var(--plate)'; }}
                onMouseLeave={(e) => { if (!active) (e.currentTarget as HTMLButtonElement).style.background = 'transparent'; }}
              >
                <div style={{ display: 'block' }}>
                  <span style={{ display: 'block', fontFamily: 'inherit', fontSize: 10, color: active ? 'rgba(255,255,255,0.55)' : 'var(--ink-3)', letterSpacing: '0.16em', marginBottom: 3 }}>
                    {String(lvl.id).padStart(2, '0')}
                  </span>
                  <span style={{ display: 'block', fontSize: 20, letterSpacing: '-0.005em', lineHeight: 1, whiteSpace: 'nowrap' }}>
                    {lvl.name}
                  </span>
                </div>
                <div style={{ marginTop: 4, fontSize: 12, color: active ? 'rgba(255,255,255,0.62)' : 'var(--ink-3)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {lvl.tagline}
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* File tree */}
      <FileTree />

      {/* Use case pinned at bottom */}
      <div style={{ marginTop: 'auto', borderTop: '1px solid var(--rule)', paddingTop: 20 }}>
        <div style={{ fontFamily: 'inherit', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 10 }}>
          The task, held constant
        </div>
        <p style={{ fontSize: 18, lineHeight: 1.32, margin: '0 0 10px', color: 'var(--ink)' }}>
          Build a <em style={{ fontStyle: 'italic', color: 'var(--accent)' }}>full-stack task manager</em> with React, FastAPI, and PostgreSQL.
        </p>
        <p style={{ fontSize: 12, color: 'var(--ink-3)', margin: 0 }}>
          Same goal, four architectures. Watch what changes.
        </p>
      </div>
    </aside>
  );
}
