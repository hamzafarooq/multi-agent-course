import type { PlanEvent } from '@lumina/contract';

/**
 * A deep search says what it is going to look for before it looks. That is the whole
 * difference between deep search and a slow quick search, and it has to be visible: a
 * reader who disagrees with the plan already knows why the answer will be wrong.
 */
export function PlanPanel({ plan }: { plan: PlanEvent | null }) {
  if (!plan) return null;

  return (
    <div className="panel">
      <h2>
        Plan <span className="count">{plan.subQuestions.length} sub-questions</span>
      </h2>
      {plan.reason ? <div className="hint" style={{ marginBottom: 8 }}>{plan.reason}</div> : null}
      <ol className="plan">
        {plan.subQuestions.map((sq) => (
          <li key={sq.i}>
            <span className="sq">{sq.i}</span>
            <div>
              {sq.question}
              {sq.reason ? <small>{sq.reason}</small> : null}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
