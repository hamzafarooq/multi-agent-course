import { useState } from 'react';
import type { AskMode, Depth } from '@lumina/contract';

export function Composer({
  onAsk,
  busy,
  spaces,
  spaceId,
  onSpace,
  deepLeft
}: {
  onAsk: (query: string, mode: AskMode, depth: Depth, spaceId?: string) => void;
  busy: boolean;
  spaces: { spaceId: string; name: string }[];
  spaceId?: string;
  onSpace: (id: string | undefined) => void;
  deepLeft?: { used: number; cap: number };
}) {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<AskMode>('auto');
  const [depth, setDepth] = useState<Depth>('quick');

  const capped = deepLeft ? deepLeft.used >= deepLeft.cap : false;

  const submit = () => {
    const q = query.trim();
    if (!q || busy) return;
    onAsk(q, mode, depth, mode === 'web' ? undefined : spaceId);
    setQuery('');
  };

  return (
    <div className="panel composer">
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
        }}
        placeholder="Ask anything. Cmd/Ctrl + Enter to send."
        aria-label="Your question"
      />
      <div className="row">
        <select value={mode} onChange={(e) => setMode(e.target.value as AskMode)} aria-label="Retrieval mode">
          <option value="auto">auto</option>
          <option value="web">web</option>
          <option value="docs">docs</option>
        </select>
        {mode !== 'web' && (
          <select
            value={spaceId ?? ''}
            onChange={(e) => onSpace(e.target.value || undefined)}
            aria-label="Space"
          >
            <option value="">no Space</option>
            {spaces.map((s) => (
              <option key={s.spaceId} value={s.spaceId}>
                {s.name}
              </option>
            ))}
          </select>
        )}
        <div className="depth" role="group" aria-label="Search depth">
          <button
            className={depth === 'quick' ? 'on' : ''}
            onClick={() => setDepth('quick')}
            aria-pressed={depth === 'quick'}
          >
            Quick
          </button>
          <button
            className={depth === 'deep' ? 'on' : ''}
            onClick={() => setDepth('deep')}
            aria-pressed={depth === 'deep'}
            disabled={capped}
            title={capped ? 'Daily deep-search cap reached' : 'Plan sub-questions, research each, merge citations'}
          >
            Deep
          </button>
        </div>
        <span className="spacer" />
        <button className="primary" onClick={submit} disabled={busy || !query.trim()}>
          {busy ? 'streaming…' : depth === 'deep' ? 'Deep search' : 'Ask'}
        </button>
      </div>
      <div className="hint">
        {depth === 'deep' ? (
          <>
            <b>Deep</b> plans sub-questions, researches each, and merges the citations. It costs
            several times a quick search and takes up to a minute
            {deepLeft ? ` — ${Math.max(0, deepLeft.cap - deepLeft.used)} of ${deepLeft.cap} left today` : ''}.
            {capped ? ' You have used today\u2019s allowance.' : ''}
          </>
        ) : (
          <>
            <code>auto</code> lets the router decide between the web and your documents; the trace
            shows what it picked and why. Switch to <b>Deep</b> for a question with several parts.
          </>
        )}
      </div>
    </div>
  );
}
