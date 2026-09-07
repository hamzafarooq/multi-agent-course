import { useEffect, useRef, useState } from 'react';
import { api } from '../api';
import { Problem } from './Notice';

type Doc = { docId: string; title: string; status: string; pct: number; pages?: number; error?: string };

/**
 * Upload returns 202 immediately; the row then walks pending → parsing → embedding →
 * indexed on the worker. A document that goes straight to `indexed` in the response is a
 * synchronous parse, which fails the assignment even when it works.
 */
export function SpacesPanel({
  spaces,
  spaceId,
  onSpace,
  onSpacesChanged
}: {
  spaces: { spaceId: string; name: string }[];
  spaceId?: string;
  onSpace: (id: string | undefined) => void;
  onSpacesChanged: () => void;
}) {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => {
    if (!spaceId) return setDocs([]);
    api
      .listDocuments(spaceId)
      .then((r) => {
        setDocs(r.documents ?? []);
        setError(null);
      })
      .catch(setError);
  };

  useEffect(load, [spaceId]);

  // Poll while anything is still working its way through the pipeline.
  useEffect(() => {
    const pending = docs.some((d) => d.status !== 'indexed' && d.status !== 'failed');
    if (!spaceId || !pending) return;
    const t = setInterval(load, 1500);
    return () => clearInterval(t);
  }, [docs, spaceId]);

  const create = async () => {
    const name = prompt('Name this Space');
    if (!name) return;
    try {
      const s = await api.createSpace(name);
      onSpacesChanged();
      onSpace(s.spaceId);
    } catch (e) {
      setError(e);
    }
  };

  const upload = async (file: File) => {
    if (!spaceId) return;
    setBusy(true);
    const started = performance.now();
    try {
      await api.uploadDocument(spaceId, file);
      // The 202 has to come back fast; the work happens after it.
      const ms = Math.round(performance.now() - started);
      if (ms > 300) console.warn(`upload accepted in ${ms}ms — the SLA for a 202 is 300ms p95`);
      load();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  return (
    <div className="panel">
      <h2>
        Spaces
        <span className="spacer" />
        <button className="tiny ghost" onClick={create}>
          + new
        </button>
      </h2>

      <select value={spaceId ?? ''} onChange={(e) => onSpace(e.target.value || undefined)} aria-label="Space">
        <option value="">no Space selected</option>
        {spaces.map((s) => (
          <option key={s.spaceId} value={s.spaceId}>
            {s.name}
          </option>
        ))}
      </select>

      {spaceId && (
        <div style={{ marginTop: 10 }}>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.md,.txt,application/pdf,text/markdown,text/plain"
            disabled={busy}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void upload(f);
            }}
          />
          <div className="hint">PDF, Markdown, or text, up to 25 MB.</div>
        </div>
      )}

      <Problem error={error} what="the Spaces routes" />

      <div style={{ marginTop: 10 }}>
        {spaceId && !docs.length && !error && <div className="empty">No documents in this Space yet.</div>}
        {docs.map((d) => (
          <div key={d.docId} className="row-item">
            <div className="grow">
              <div className="trunc" title={d.title}>
                {d.title}
              </div>
              <small>
                {d.pages ? `${d.pages} pages · ` : ''}
                {d.error ?? d.docId}
              </small>
              {d.status !== 'indexed' && d.status !== 'failed' && (
                <div className="bar">
                  <i style={{ width: `${Math.max(3, d.pct)}%` }} />
                </div>
              )}
            </div>
            <span className={`status ${d.status}`}>{d.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
