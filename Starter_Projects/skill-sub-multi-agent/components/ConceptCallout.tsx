'use client';

import { useState } from 'react';
import { LevelDef } from '@/lib/demo-data';

export default function ConceptCallout({ level }: { level: LevelDef }) {
  const [tab, setTab] = useState<'what' | 'how'>('what');

  return (
    <div style={{ border: '1px solid var(--rule)', borderRadius: 2, background: 'var(--surface)' }}>
      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--rule)' }} role="tablist">
        {(['what', 'how'] as const).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => setTab(t)}
            style={{
              appearance: 'none',
              background: 'transparent',
              border: 0,
              borderBottom: `2px solid ${tab === t ? 'var(--accent)' : 'transparent'}`,
              padding: '14px 20px',
              marginBottom: -1,
              cursor: 'pointer',
              fontSize: 13,
              color: tab === t ? 'var(--ink)' : 'var(--ink-3)',
              letterSpacing: '0.005em',
              transition: 'color 120ms ease',
            }}
          >
            {t === 'what' ? "What's happening" : 'How to write it'}
          </button>
        ))}
      </div>

      {/* Body */}
      <div style={{ padding: '20px 24px 22px' }}>
        {tab === 'what' ? (
          <div>
            <p style={{ fontFamily: 'inherit', fontSize: 19, lineHeight: 1.42, color: 'var(--ink)', margin: '0 0 14px', maxWidth: '60ch' }}>
              {level.explanation}
            </p>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, borderTop: '1px dashed var(--rule)', paddingTop: 12 }}>
              <span style={{ fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--ink-3)', flexShrink: 0 }}>
                analogy
              </span>
              <span style={{ fontSize: 13.5, color: 'var(--ink-2)', fontStyle: 'italic' }}>
                {level.analogy}
              </span>
            </div>
          </div>
        ) : (
          <pre style={{ margin: 0, fontFamily: 'inherit', fontSize: 12.5, lineHeight: 1.55, color: 'var(--ink)', whiteSpace: 'pre', overflowX: 'auto', background: 'var(--plate)', padding: '16px 18px', borderRadius: 2, border: '1px solid var(--rule-2)' }}>
            <code>{level.code}</code>
          </pre>
        )}
      </div>
    </div>
  );
}
