import { useEffect, useState } from 'react';
import { EvalsReport, type GateResult, type RubricRow, type SlaRow, type Trajectory } from '@lumina/contract';
import { api } from './api';
import { Problem } from './components/Notice';

/**
 * /evals — the Product Evaluation. THIS PAGE IS THE SUBMISSION (SUBMISSION.md).
 *
 * It renders whatever `GET /evals/report.json` returns and nothing else. It has no way
 * to compute a score, on purpose: every number here came from a run of the gates against
 * the deployed app, written by the eval skill. Nothing on this page is hand-written, and
 * a number a run did not produce is an automatic fail.
 */
export function EvalsPage({ report: injected }: { report?: EvalsReport } = {}) {
  const [report, setReport] = useState<EvalsReport | null>(injected ?? null);
  const [raw, setRaw] = useState<unknown>(null);
  const [error, setError] = useState<unknown>(null);
  const [schemaIssue, setSchemaIssue] = useState<string | null>(null);

  useEffect(() => {
    // `injected` exists so the page can be rendered from a fixture in a test without a
    // server. In the product it is always undefined and the report comes off the gateway.
    if (injected) return;
    api
      .evalsReport()
      .then((body) => {
        setRaw(body);
        const parsed = EvalsReport.safeParse(body);
        if (parsed.success) setReport(parsed.data);
        else setSchemaIssue(parsed.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join(' · '));
      })
      .catch(setError);
  }, [injected]);

  if (error) {
    return (
      <Shell>
        <Problem error={error} what="GET /evals/report.json" />
        <p className="empty">
          Run <code>/fde-lumina-eval --deploy-url https://&lt;your-gateway&gt;</code> in Claude Code.
          It runs the six gates against the deployed app and writes the report this page renders.
        </p>
      </Shell>
    );
  }

  if (!report) {
    return (
      <Shell>
        {schemaIssue ? (
          <div className="notice bad">
            <b>report.json does not match the contract</b> — {schemaIssue}
            <p>
              The shape is <code>EvalsReport</code> in <code>packages/contract</code>. Do not
              hand-edit the file; re-run the eval.
            </p>
            <pre style={{ overflowX: 'auto', fontSize: 12 }}>{JSON.stringify(raw, null, 2).slice(0, 2000)}</pre>
          </div>
        ) : (
          <div className="empty">Loading the evaluation…</div>
        )}
      </Shell>
    );
  }

  const { rubric, bench, quality, trajectories } = report;
  const pct = rubric.total ? Math.round((rubric.awarded / rubric.total) * 100) : 0;

  return (
    <Shell>
      <h1>
        {report.assignment} · {report.student}
      </h1>
      <div className="sub">
        deployed {new Date(report.deployedAt).toLocaleString()}
        {report.repo ? ' · ' : ''}
        {report.repo ? <a href={report.repo}>repo</a> : null}
        {report.runNotes ? ` · ${report.runNotes}` : ''}
      </div>

      <div className="score">
        <span className="big">{rubric.awarded}</span>
        <span className="of">/ {rubric.total} · {pct}%</span>
        <span className="spacer" />
        <span className={`pill ${bench.pass ? 'done' : 'error'}`}>bench {bench.pass ? 'pass' : 'fail'}</span>
        <span className={`pill ${quality.errors ? 'error' : quality.warnings ? 'cap' : 'done'}`}>
          quality {quality.errors} error / {quality.warnings} warn
        </span>
      </div>

      {report.video ? (
        <Section title="Demo">
          <div className="video">
            <iframe src={embedUrl(report.video)} title="demo" allow="fullscreen; picture-in-picture" allowFullScreen />
          </div>
          {/* A blocked embed (shields, corporate proxy) must not hide the link itself. */}
          <p className="sub" style={{ marginTop: 8 }}>
            If the player is blocked, open it directly:{' '}
            <a href={report.video} target="_blank" rel="noreferrer noopener">
              {report.video}
            </a>
          </p>
        </Section>
      ) : null}

      {report.gates.length ? (
      <Section title="Gates">
        <table>
          <thead>
            <tr>
              <th className="num">#</th>
              <th>Gate</th>
              <th>Status</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            {report.gates.map((g: GateResult) => (
              <tr key={g.gate} className={g.status === 'fail' ? 'fail' : undefined}>
                <td className="num">{g.gate}</td>
                <td>{g.name}</td>
                <td>{mark(g.status)}</td>
                <td>{g.detail ?? ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
      ) : null}

      <Section title="Rubric">
        <RubricTable rows={rubric.automated} caption="Automated" />
        <RubricTable rows={rubric.manual} caption="Manual" />
        {rubric.redLines.length ? (
          <table>
            <thead>
              <tr>
                <th>Red line</th>
                <th>OK</th>
              </tr>
            </thead>
            <tbody>
              {rubric.redLines.map((r, i) => (
                <tr key={i} className={r.ok ? undefined : 'fail'}>
                  <td>{r.check}</td>
                  <td>
                    {r.ok ? <span className="tick">✓</span> : <span className="cross">✗ {r.detail ?? ''}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </Section>

      <Section title="Benchmark against the declared SLA">
        <div className="sub">
          {bench.target} · ran {new Date(bench.ranAt).toLocaleString()}
        </div>
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th className="num">Target</th>
              <th className="num">Actual</th>
              <th>Pass</th>
            </tr>
          </thead>
          <tbody>
            {bench.sla.map((r: SlaRow) => (
              <tr key={r.metric} className={r.pass ? undefined : 'fail'}>
                <td>{r.metric}</td>
                <td className="num">
                  {r.comparator} {r.target}
                  {r.unit}
                </td>
                <td className="num">{r.actual === null ? '—' : `${round(r.actual)}${r.unit}`}</td>
                <td>{r.pass ? <span className="tick">✓</span> : <span className="cross">✗</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Quality gates (rule by rule)">
        <table>
          <thead>
            <tr>
              <th>Rule</th>
              <th>Title</th>
              <th>Severity</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {quality.results.map((r) => (
              <tr key={r.id} className={r.status === 'fail' && r.severity === 'error' ? 'fail' : undefined}>
                <td>
                  <code>{r.id}</code>
                </td>
                <td>{r.title}</td>
                <td>{r.severity}</td>
                <td>
                  {mark(r.status)} {r.detail ?? ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Design: the five questions">
        <dl className="design">
          <dt>Components</dt>
          <dd>{report.design.components}</dd>
          <dt>Responsibilities</dt>
          <dd>{report.design.responsibilities}</dd>
          <dt>Communication</dt>
          <dd>{report.design.communication}</dd>
          <dt>State</dt>
          <dd>{report.design.state}</dd>
          <dt>Trade-offs</dt>
          <dd>{report.design.tradeoffs}</dd>
        </dl>
      </Section>

      <Section title="Trajectories read end to end">
        <TrajectoryView label="Successful" t={trajectories.successful} />
        <TrajectoryView label="Failing" t={trajectories.failing} />
      </Section>

      <p className="sub" style={{ marginTop: 28 }}>
        Machine-readable: <a href="/evals/report.json">/evals/report.json</a>
      </p>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="topbar">
        <div className="brand">
          LUM<span>INA</span>
        </div>
        <nav>
          <a href="/">Ask</a>
          <a href="/evals" className="on">
            Evals
          </a>
        </nav>
      </header>
      <div className="evals">{children}</div>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginTop: 26 }}>
      <h2 style={{ fontSize: 12, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--ink-faint)' }}>
        {title}
      </h2>
      {children}
    </section>
  );
}

function RubricTable({ rows, caption }: { rows: RubricRow[]; caption: string }) {
  if (!rows.length) return null;
  return (
    <table style={{ marginBottom: 14 }}>
      <thead>
        <tr>
          <th>{caption}</th>
          <th className="num">Pts</th>
          <th className="num">Awarded</th>
          <th>Status</th>
          <th>Evidence</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} className={r.status === 'fail' ? 'fail' : undefined}>
            <td>{r.label}</td>
            <td className="num">{r.points}</td>
            <td className="num">{r.awarded}</td>
            <td>{mark(r.status)}</td>
            <td>{r.evidence}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TrajectoryView({ label, t }: { label: string; t: Trajectory }) {
  return (
    <div className="traj">
      <h4>
        {label} · <code>{t.requestId}</code>
        {t.terminated ? <span className={`pill ${t.terminated}`}> {t.terminated}</span> : null}
      </h4>
      {t.query ? <div className="sub">{t.query}</div> : null}
      <div className="trace">
        {t.steps.map((s) => (
          <div key={s.step} className={`step${s.ok ? '' : ' bad'}`}>
            <span className="ix">{s.step}</span>
            <span className="tool">{s.tool}</span>
            <span className="why">{s.ok ? (s.reason ?? '') : <span className="err">{s.error ?? 'failed'}</span>}</span>
            {s.ms !== undefined ? <span className="ms">{Math.round(s.ms)}ms</span> : null}
          </div>
        ))}
      </div>
      <div className="notes">{t.notes}</div>
    </div>
  );
}

const mark = (status: string) =>
  status === 'pass' ? (
    <span className="tick">✓ pass</span>
  ) : status === 'fail' ? (
    <span className="cross">✗ fail</span>
  ) : status === 'partial' ? (
    <span className="warnmark">◐ partial</span>
  ) : (
    <span className="empty">{status}</span>
  );

const round = (n: number) => (Number.isInteger(n) ? n : Number(n.toFixed(3)));

/** youtu.be, youtube.com/watch and loom share links all need rewriting before they embed. */
function embedUrl(url: string): string {
  const yt = /(?:youtu\.be\/|youtube\.com\/watch\?v=)([\w-]{11})/.exec(url);
  if (yt) return `https://www.youtube.com/embed/${yt[1]}`;
  const loom = /loom\.com\/share\/([\w]+)/.exec(url);
  if (loom) return `https://www.loom.com/embed/${loom[1]}`;
  return url;
}
