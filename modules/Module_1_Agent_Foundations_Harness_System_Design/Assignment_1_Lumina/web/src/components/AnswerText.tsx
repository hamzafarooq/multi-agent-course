import type { Source } from '@lumina/contract';

/**
 * Renders the answer with every `[n]` as a chip. A chip whose number has no matching
 * source is drawn red: an ungrounded citation should be visible in the product, not only
 * in a grader's report.
 */
export function AnswerText({
  text,
  sources,
  onCite
}: {
  text: string;
  sources: Source[];
  onCite: (n: number) => void;
}) {
  const have = new Set(sources.map((s) => s.n));
  const parts = text.split(/(\[\d{1,3}\])/g);

  return (
    <div className="answer-text">
      {parts.map((part, i) => {
        const m = /^\[(\d{1,3})\]$/.exec(part);
        if (!m) return <span key={i}>{part}</span>;
        const n = Number(m[1]);
        const known = have.has(n);
        return (
          <span
            key={i}
            className={`cite${known ? '' : ' dangling'}`}
            title={known ? sources.find((s) => s.n === n)?.title : `[${n}] resolves to nothing retrieved in this request`}
            onClick={() => known && onCite(n)}
            role={known ? 'button' : undefined}
          >
            {n}
          </span>
        );
      })}
    </div>
  );
}
