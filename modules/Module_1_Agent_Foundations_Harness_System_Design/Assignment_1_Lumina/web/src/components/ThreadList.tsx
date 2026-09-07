export function ThreadList({
  threads,
  current,
  onPick,
  onNew
}: {
  threads: { threadId: string; title: string }[];
  current?: string;
  onPick: (id: string) => void;
  onNew: () => void;
}) {
  return (
    <div className="panel">
      <h2>
        Threads
        <span className="spacer" />
        <button className="tiny ghost" onClick={onNew}>
          + new
        </button>
      </h2>
      {!threads.length && <div className="empty">A new thread is created when you ask your first question.</div>}
      {threads.map((t) => (
        <button
          key={t.threadId}
          className={`thread-btn${t.threadId === current ? ' on' : ''}`}
          onClick={() => onPick(t.threadId)}
        >
          <span className="trunc" style={{ display: 'block' }}>
            {t.title || t.threadId}
          </span>
        </button>
      ))}
    </div>
  );
}
