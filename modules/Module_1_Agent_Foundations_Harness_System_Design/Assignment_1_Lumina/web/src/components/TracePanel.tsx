import type { TraceEvent } from '@lumina/contract';

/**
 * The trace is the debugging surface. A grader must be able to reconstruct why an answer
 * cited what it cited from this alone, so a failed step shows its error string rather
 * than disappearing.
 */
export function TracePanel({ steps }: { steps: TraceEvent[] }) {
  return (
    <div className="panel">
      <h2>
        Trace <span className="count">{steps.length || ''}</span>
      </h2>
      {!steps.length && <div className="empty">Every tool call the loop makes will show up here, in order.</div>}
      <div className="trace">
        {steps.map((s, i) => (
          <div key={`${s.step}-${i}`} className={`step${s.ok ? '' : ' bad'}`}>
            <span className="ix">{s.step}</span>
            {/* On a deep search, which sub-question this step was serving. */}
            {s.subQuestion ? <span className="sq" title={`sub-question ${s.subQuestion}`}>{s.subQuestion}</span> : null}
            <span className="tool">{s.tool}</span>
            <span className="why">{s.ok ? (s.reason ?? '') : <span className="err">{s.error ?? 'failed'}</span>}</span>
            <span className="ms">{Math.round(s.ms)}ms</span>
          </div>
        ))}
      </div>
    </div>
  );
}
