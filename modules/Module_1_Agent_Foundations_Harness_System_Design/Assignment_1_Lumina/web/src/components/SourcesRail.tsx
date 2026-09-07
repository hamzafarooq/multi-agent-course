import type { Source } from '@lumina/contract';

const docLabel = (s: Source) => {
  const p = s.locator?.page;
  if (p) return `${s.title}, p. ${p}`;
  if (s.locator?.heading) return `${s.title} — ${s.locator.heading}`;
  if (s.locator?.line) return `${s.title}, line ${s.locator.line}`;
  return s.title;
};

export function SourcesRail({ sources, highlight }: { sources: Source[]; highlight?: number }) {
  return (
    <div className="panel">
      <h2>
        Sources <span className="count">{sources.length || ''}</span>
      </h2>
      {!sources.length && <div className="empty">Citations appear here before the text starts arriving.</div>}
      {sources.map((s) => (
        <div key={s.n} id={`src-${s.n}`} className={`source${highlight === s.n ? ' hl' : ''}`}>
          <div className="n">{s.n}</div>
          <div className="grow">
            <div className="title">
              {s.kind === 'web' && s.url ? (
                <a href={s.url} target="_blank" rel="noreferrer noopener">
                  {s.title}
                </a>
              ) : (
                docLabel(s)
              )}
            </div>
            <div className="meta">
              {s.subQuestion ? <span className="sq-inline">sub-question {s.subQuestion}</span> : null}
              {s.kind === 'web' ? (s.url ?? '') : `doc · ${s.docId ?? ''}`}
            </div>
            <div className="snip">{s.snippet}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
