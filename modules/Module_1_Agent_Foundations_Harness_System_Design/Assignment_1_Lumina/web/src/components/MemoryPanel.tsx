import { useEffect, useState } from 'react';
import { api } from '../api';
import { Problem } from './Notice';

/**
 * Nothing is remembered that this panel does not show. That is the whole point: memory
 * you cannot inspect and delete is not memory, it is a leak.
 */
export function MemoryPanel({ refreshKey }: { refreshKey: number }) {
  const [memories, setMemories] = useState<{ id: string; text: string; createdAt: string }[]>([]);
  const [error, setError] = useState<unknown>(null);

  const load = () => {
    api
      .listMemory()
      .then((r) => {
        setMemories(r.memories ?? []);
        setError(null);
      })
      .catch(setError);
  };

  useEffect(load, [refreshKey]);

  const remove = async (id: string) => {
    try {
      await api.deleteMemory(id);
      load();
    } catch (e) {
      setError(e);
    }
  };

  return (
    <div className="panel">
      <h2>
        Memory <span className="count">{memories.length || ''}</span>
        <span className="spacer" />
        <button className="tiny ghost" onClick={load}>
          refresh
        </button>
      </h2>
      <Problem error={error} what="GET /memory" />
      {!error && !memories.length && (
        <div className="empty">
          Empty. Tell it a preference (&ldquo;always answer in British English&rdquo;) and it should
          land here — then carry into a new thread.
        </div>
      )}
      {memories.map((m) => (
        <div key={m.id} className="row-item">
          <div className="grow">
            {m.text}
            <small>{new Date(m.createdAt).toLocaleString()}</small>
          </div>
          <button className="tiny" onClick={() => remove(m.id)} title="Delete this memory">
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
