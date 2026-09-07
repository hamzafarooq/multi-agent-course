import { useCallback, useEffect, useState } from 'react';
import type { AskMode, Depth, DoneEvent, PlanEvent, Source, TraceEvent } from '@lumina/contract';
import { api, ApiError, askStream, setUserId, userId } from './api';
import { Composer } from './components/Composer';
import { AnswerText } from './components/AnswerText';
import { SourcesRail } from './components/SourcesRail';
import { TracePanel } from './components/TracePanel';
import { ThreadList } from './components/ThreadList';
import { MemoryPanel } from './components/MemoryPanel';
import { SpacesPanel } from './components/SpacesPanel';
import { PlanPanel } from './components/PlanPanel';
import { Problem } from './components/Notice';

type UiMessage = {
  role: 'user' | 'assistant';
  content: string;
  sources: Source[];
  trace: TraceEvent[];
  plan?: PlanEvent;
  depth?: Depth;
  answerId?: string;
  done?: DoneEvent;
  streaming?: boolean;
};

export function App({ route }: { route: 'app' | 'evals' }) {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [threads, setThreads] = useState<{ threadId: string; title: string }[]>([]);
  const [threadId, setThreadId] = useState<string | undefined>();
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [spaces, setSpaces] = useState<{ spaceId: string; name: string }[]>([]);
  const [spaceId, setSpaceId] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [memoryKey, setMemoryKey] = useState(0);
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [highlight, setHighlight] = useState<number | undefined>();
  const [uid, setUid] = useState(userId());

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  // The deep-search allowance is server-side truth; the composer only reflects it.
  const loadStats = useCallback(() => {
    api.stats().then(setStats).catch(() => setStats(null));
  }, []);
  useEffect(loadStats, [loadStats, uid]);

  const loadThreads = useCallback(() => {
    api
      .listThreads()
      .then((r) => setThreads(r.threads ?? []))
      // The thread list is a convenience; a 501 here must not blank the page.
      .catch(() => setThreads([]));
  }, []);

  const loadSpaces = useCallback(() => {
    api
      .listSpaces()
      .then((r) => setSpaces(r.spaces ?? []))
      .catch(() => setSpaces([]));
  }, []);

  useEffect(() => {
    loadThreads();
    loadSpaces();
  }, [loadThreads, loadSpaces, uid]);

  const openThread = async (id: string) => {
    setThreadId(id);
    setError(null);
    try {
      const r = await api.getThread(id);
      const rows = (r.messages ?? []) as {
        role: 'user' | 'assistant';
        content: string;
        sources?: Source[];
        answerId?: string;
      }[];
      setMessages(
        rows.map((m) => ({
          role: m.role,
          content: m.content,
          sources: m.sources ?? [],
          trace: [],
          answerId: m.answerId
        }))
      );
    } catch (e) {
      setMessages([]);
      setError(e);
    }
  };

  const newThread = () => {
    setThreadId(undefined);
    setMessages([]);
    setError(null);
  };

  const patchLast = (patch: (m: UiMessage) => UiMessage) =>
    setMessages((prev) => {
      if (!prev.length) return prev;
      const next = prev.slice();
      next[next.length - 1] = patch(next[next.length - 1]!);
      return next;
    });

  const ask = async (query: string, mode: AskMode, depth: Depth, space?: string) => {
    setBusy(true);
    setError(null);

    let id = threadId;
    try {
      if (!id) {
        id = (await api.createThread()).threadId;
        setThreadId(id);
      }
    } catch (e) {
      setError(e);
      setBusy(false);
      return;
    }

    setMessages((prev) => [
      ...prev,
      { role: 'user', content: query, sources: [], trace: [] },
      { role: 'assistant', content: '', sources: [], trace: [], depth, streaming: true }
    ]);

    try {
      await askStream(
        id,
        { query, mode, depth, spaceId: space },
        {
          // On a deep search this lands before anything is retrieved.
          onPlan: (p) => patchLast((m) => ({ ...m, plan: p })),
          onTrace: (t) => patchLast((m) => ({ ...m, trace: [...m.trace, t] })),
          // sources arrive before the first token, so the chips can resolve as text lands
          onSources: (s) => patchLast((m) => ({ ...m, sources: s })),
          onToken: (text) => patchLast((m) => ({ ...m, content: m.content + text })),
          onDone: (d) =>
            patchLast((m) => ({ ...m, done: d, answerId: d.answerId, streaming: false })),
          onError: (e) => {
            patchLast((m) => ({ ...m, streaming: false }));
            setError(new ApiError(e.status, e.error));
          }
        }
      );
    } catch (e) {
      patchLast((m) => ({ ...m, streaming: false }));
      setError(e);
    } finally {
      setBusy(false);
      setMemoryKey((k) => k + 1);
      loadThreads();
      loadStats();
    }
  };

  const last = messages[messages.length - 1];
  const sources = last?.sources ?? [];
  const trace = last?.trace ?? [];
  const plan = last?.plan ?? null;
  const deepLeft =
    stats && typeof stats.deepDailyCap === 'number'
      ? { used: stats.deepToday ?? 0, cap: stats.deepDailyCap }
      : undefined;

  if (route === 'evals') return null;

  return (
    <>
      <header className="topbar">
        <div className="brand">
          LUM<span>INA</span>
        </div>
        <nav>
          <a href="/" className="on">
            Ask
          </a>
          <a href="/evals">Evals</a>
        </nav>
        <span className="spacer" />
        <div className="userbox">
          <label htmlFor="uid">X-User-Id</label>
          <input
            id="uid"
            defaultValue={uid}
            onBlur={(e) => {
              setUserId(e.target.value);
              setUid(userId());
              newThread();
            }}
          />
        </div>
        <div className="health" title="GET /health">
          <span className={`dot ${health?.status === 'ok' ? 'ok' : health ? 'bad' : ''}`} />
          {health
            ? `${health.model ?? '?'} · ${health.searchProvider ?? '?'} · ${health.vectorStore ?? '?'} · db ${health.db ?? '?'}`
            : 'gateway unreachable'}
        </div>
      </header>

      <main className="layout">
        <div className="rail-left">
          <ThreadList threads={threads} current={threadId} onPick={openThread} onNew={newThread} />
          <SpacesPanel
            spaces={spaces}
            spaceId={spaceId}
            onSpace={setSpaceId}
            onSpacesChanged={loadSpaces}
          />
        </div>

        <div>
          <Composer
            onAsk={ask}
            busy={busy}
            spaces={spaces}
            spaceId={spaceId}
            onSpace={setSpaceId}
            deepLeft={deepLeft}
          />

          {error ? (
            <div style={{ marginTop: 12 }}>
              <Problem error={error} what="POST /threads/{id}/ask" />
            </div>
          ) : null}

          {!messages.length && !error && (
            <div className="panel" style={{ marginTop: 12 }}>
              <h2>Nothing asked yet</h2>
              <div className="empty">
                Ask a question and the answer streams in with citations you can click. Until the
                backend implements a route you will see a <code>501 not implemented yet</code> notice
                instead — that is the intended starting state.
              </div>
            </div>
          )}

          <div className="thread" style={{ marginTop: 12 }}>
            {messages.map((m, i) =>
              m.role === 'user' ? (
                <div key={i} className="msg user">
                  <header>you</header>
                  <div className="body">{m.content}</div>
                </div>
              ) : (
                <div key={i} className="msg">
                  <header>
                    lumina
                    {m.depth === 'deep' || m.done?.depth === 'deep' ? <span className="pill deep">deep</span> : null}
                    {m.done ? <span className={`pill ${m.done.terminated}`}>{m.done.terminated}</span> : null}
                  </header>
                  <div className="body">
                    <AnswerText text={m.content} sources={m.sources} onCite={setHighlight} />
                    {m.streaming ? <span className="caret" /> : null}
                  </div>
                  {m.done ? (
                    <div className="donebar">
                      <span>
                        ttft <b>{Math.round(m.done.ttftMs)}ms</b>
                      </span>
                      <span>
                        total <b>{Math.round(m.done.latencyMs)}ms</b>
                      </span>
                      <span>
                        tokens{' '}
                        <b>
                          {m.done.tokens.in}/{m.done.tokens.out}
                        </b>
                      </span>
                      <span>
                        cost <b>${m.done.costUsd.toFixed(4)}</b>
                      </span>
                      <span>
                        cache <b>{m.done.searchCached ? 'hit' : 'miss'}</b>
                      </span>
                      {m.done.subQuestions ? (
                        <span>
                          sub-questions <b>{m.done.subQuestions}</b>
                        </span>
                      ) : null}
                      <span>{m.done.model}</span>
                    </div>
                  ) : null}
                </div>
              )
            )}
          </div>
        </div>

        <div className="rail-right">
          <PlanPanel plan={plan} />
          <SourcesRail sources={sources} highlight={highlight} />
          <TracePanel steps={trace} />
          <MemoryPanel refreshKey={memoryKey} />
        </div>
      </main>
    </>
  );
}
