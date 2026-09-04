'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { AgentDef, AgentStatus, LevelDef } from '@/lib/demo-data';
import AgentNode, { NODE_W, NODE_H } from './AgentNode';

const CANVAS_W = 720;
const CANVAS_H = 440;
const TIP_W = 300;

function inlineMd(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/);
  return parts.map((p, i) => {
    if (p.startsWith('**') && p.endsWith('**'))
      return <strong key={i} style={{ color: '#fff', fontWeight: 600 }}>{p.slice(2, -2)}</strong>;
    if (p.startsWith('`') && p.endsWith('`'))
      return <code key={i} style={{ fontFamily: 'monospace', fontSize: 11.5, background: 'rgba(255,255,255,0.12)', padding: '1px 5px', borderRadius: 3 }}>{p.slice(1, -1)}</code>;
    return p;
  });
}

function renderMd(md: string): React.ReactNode[] {
  const lines = md.split('\n');
  const out: React.ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith('```')) {
      const code: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) { code.push(lines[i]); i++; }
      out.push(<pre key={i} style={{ margin: '10px 0', background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 4, padding: '10px 14px', fontSize: 11.5, lineHeight: 1.55, overflowX: 'auto', fontFamily: 'monospace', color: 'rgba(255,255,255,0.9)' }}><code>{code.join('\n')}</code></pre>);
    } else if (line.startsWith('### ')) {
      out.push(<h3 key={i} style={{ margin: '16px 0 5px', fontSize: 12, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.55)', fontWeight: 500 }}>{line.slice(4)}</h3>);
    } else if (line.startsWith('## ')) {
      out.push(<h2 key={i} style={{ margin: '0 0 12px', fontSize: 18, letterSpacing: '-0.01em', fontWeight: 600, color: '#fff' }}>{line.slice(3)}</h2>);
    } else if (line.startsWith('- ')) {
      const items: string[] = [];
      while (i < lines.length && lines[i].startsWith('- ')) { items.push(lines[i].slice(2)); i++; }
      out.push(<ul key={i} style={{ margin: '6px 0', paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 4 }}>{items.map((it, j) => <li key={j} style={{ fontSize: 13, lineHeight: 1.5, color: 'rgba(255,255,255,0.85)' }}>{inlineMd(it)}</li>)}</ul>);
      continue;
    } else if (line.trim()) {
      out.push(<p key={i} style={{ margin: '0 0 10px', fontSize: 13.5, lineHeight: 1.6, color: 'rgba(255,255,255,0.88)' }}>{inlineMd(line)}</p>);
    }
    i++;
  }
  return out;
}

function NodeDetailModal({ agent, onClose }: { agent: AgentDef; onClose: () => void }) {
  const roleLabel: Record<string, string> = { human: 'Human', orch: 'Orchestrator', merge: 'Synthesiser', main: 'Main agent', sub: 'Sub-agent', single: 'Skill' };
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);
  return (
    <div
      onClick={onClose}
      style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)', WebkitBackdropFilter: 'blur(4px)' }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: 480, maxHeight: '82vh', display: 'flex', flexDirection: 'column', background: 'rgba(26,24,21,0.97)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 6, boxShadow: '0 24px 60px -10px rgba(0,0,0,0.7)', animation: 'tipfade 160ms ease both', overflow: 'hidden' }}
      >
        {/* Sticky header — never scrolls away */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '18px 24px 14px', flexShrink: 0, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <span style={{ fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', fontWeight: 500 }}>{roleLabel[agent.role] ?? 'Agent'} · {agent.name}</span>
          <button onClick={onClose} style={{ appearance: 'none', background: 'transparent', border: 0, cursor: 'pointer', color: 'rgba(255,255,255,0.45)', fontSize: 18, lineHeight: 1, padding: '0 2px' }}>×</button>
        </div>
        {/* Scrollable body — padding lives here so bottom padding is always reachable */}
        <div style={{ overflowY: 'auto', padding: '20px 28px 32px', flex: 1 }}>
          {agent.detail ? renderMd(agent.detail) : <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13 }}>{agent.brief}</p>}
        </div>
      </div>
    </div>
  );
}

interface NodeState {
  status: AgentStatus;
  output?: string;
}

interface Props {
  level: LevelDef;
}

function nodeCenter(agent: AgentDef) {
  return { cx: agent.x + NODE_W / 2, cy: agent.y + NODE_H / 2 };
}

function connectionPath(from: AgentDef, to: AgentDef): string {
  const a = nodeCenter(from);
  const b = nodeCenter(to);
  const dx = b.cx - a.cx;
  const dy = b.cy - a.cy;
  let x1 = a.cx, y1 = a.cy, x2 = b.cx, y2 = b.cy;

  if (Math.abs(dy) > Math.abs(dx)) {
    y1 = a.cy + Math.sign(dy) * (NODE_H / 2);
    y2 = b.cy - Math.sign(dy) * (NODE_H / 2);
  } else {
    x1 = a.cx + Math.sign(dx) * (NODE_W / 2);
    x2 = b.cx - Math.sign(dx) * (NODE_W / 2);
  }

  const midY = (y1 + y2) / 2;
  return `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
}

function Tooltip({ agent, state, canvasRef }: { agent: AgentDef; state?: NodeState; canvasRef: React.RefObject<HTMLDivElement | null> }) {
  const status = state?.status ?? 'idle';
  const output = state?.output;

  const nodeCx = agent.x + NODE_W / 2;
  const nodeCy = agent.y + NODE_H / 2;
  const inTopThird = nodeCy < CANVAS_H * 0.35;
  const inBottomThird = nodeCy > CANVAS_H * 0.65;

  let tipStyle: React.CSSProperties = {};
  if (inBottomThird) {
    tipStyle = {
      left: Math.max(8, Math.min(nodeCx - TIP_W / 2, CANVAS_W - TIP_W - 8)),
      bottom: CANVAS_H - agent.y + 10,
    };
  } else if (inTopThird) {
    tipStyle = {
      left: Math.max(8, Math.min(nodeCx - TIP_W / 2, CANVAS_W - TIP_W - 8)),
      top: agent.y + NODE_H + 10,
    };
  } else {
    const goLeft = nodeCx > CANVAS_W / 2;
    tipStyle = goLeft
      ? { right: CANVAS_W - agent.x + 12, top: Math.max(8, Math.min(nodeCy - 60, CANVAS_H - 240)) }
      : { left: agent.x + NODE_W + 12, top: Math.max(8, Math.min(nodeCy - 60, CANVAS_H - 240)) };
  }

  const roleLabel: Record<string, string> = {
    human: 'Human',
    orch: 'Orchestrator',
    merge: 'Synthesiser',
    main: 'Main agent',
    sub: 'Sub-agent',
    single: 'Skill',
  };

  const statusColor =
    status === 'thinking' ? 'oklch(0.78 0.15 50)' : status === 'done' ? 'oklch(0.82 0.12 145)' : 'rgba(255,255,255,0.82)';

  return (
    <div
      role="tooltip"
      style={{
        position: 'absolute',
        ...tipStyle,
        zIndex: 10,
        width: TIP_W,
        background: 'rgba(26,24,21,0.8)',
        backdropFilter: 'blur(10px) saturate(140%)',
        WebkitBackdropFilter: 'blur(10px) saturate(140%)',
        color: '#FBFAF5',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 4,
        padding: '13px 16px 15px',
        boxShadow: '0 1px 0 rgba(0,0,0,0.08), 0 18px 40px -10px rgba(0,0,0,0.5)',
        animation: 'tipfade 140ms ease both',
        pointerEvents: 'none',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <div style={{ fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.65)', fontWeight: 500 }}>
          {roleLabel[agent.role] ?? 'Agent'}
        </div>
        <div style={{ fontSize: 10, letterSpacing: '0.16em', textTransform: 'uppercase', padding: '2px 7px', borderRadius: 2, border: `1px solid ${statusColor}`, color: statusColor, fontWeight: 500 }}>
          {status}
        </div>
      </div>

      <div style={{ fontSize: 17, fontWeight: 600, letterSpacing: '-0.01em', lineHeight: 1.15, marginBottom: 8, color: '#ffffff' }}>
        {agent.name}
      </div>

      {agent.brief && (
        <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: 'rgba(255,255,255,0.92)', fontWeight: 400 }}>
          {agent.brief}
        </p>
      )}

      {output && (
        <>
          <div style={{ margin: '12px 0 7px', display: 'flex', alignItems: 'center', gap: 8, fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.55)', fontWeight: 500 }}>
            <span>returned</span>
            <span style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.2)' }} />
          </div>
          <pre style={{ margin: 0, fontFamily: 'inherit', fontSize: 11.5, lineHeight: 1.55, color: 'rgba(255,255,255,0.95)', whiteSpace: 'pre-wrap', maxHeight: 160, overflow: 'hidden', maskImage: 'linear-gradient(to bottom, #000 78%, transparent)', WebkitMaskImage: 'linear-gradient(to bottom, #000 78%, transparent)' }}>
            {output}
          </pre>
        </>
      )}

      {!output && status === 'thinking' && (
        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'rgba(255,255,255,0.75)' }}>
          {[0, 0.15, 0.30].map((delay, i) => (
            <span key={i} style={{ width: 4, height: 4, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block', animation: `tipdot 1s ease-in-out ${delay}s infinite` }} />
          ))}
          <span>working…</span>
        </div>
      )}
    </div>
  );
}

export default function SimulationView({ level }: Props) {
  const [nodeStates, setNodeStates] = useState<Record<string, NodeState>>({});
  const [activeConns, setActiveConns] = useState<Set<string>>(new Set());
  const [running, setRunning] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [finalOutput, setFinalOutput] = useState<{ agentName: string; text: string } | null>(null);
  const [currentStep, setCurrentStep] = useState(-1);
  const [hovered, setHovered] = useState<AgentDef | null>(null);
  const [clicked, setClicked] = useState<AgentDef | null>(null);
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const canvasRef = useRef<HTMLDivElement>(null);

  const clearAllTimeouts = () => {
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];
  };

  const reset = useCallback(() => {
    clearAllTimeouts();
    setNodeStates({});
    setActiveConns(new Set());
    setRunning(false);
    setCompleted(false);
    setFinalOutput(null);
    setCurrentStep(-1);
    setHovered(null);
  }, []);

  useEffect(() => { reset(); }, [level.id, reset]);

  const run = useCallback(() => {
    if (running) return;
    reset();
    setRunning(true);

    let cumulative = 0;
    level.steps.forEach((step, idx) => {
      cumulative += step.delay;

      const t = setTimeout(() => {
        setCurrentStep(idx);

        setNodeStates((prev) => ({
          ...prev,
          [step.agentId]: {
            status: step.status,
            output: step.output ?? prev[step.agentId]?.output,
          },
        }));

        const activatedKeys: string[] = [];
        level.connections.forEach((c, i) => {
          const key = `${c.from}->${c.to}-${i}`;
          if (step.status === 'thinking' && c.to === step.agentId) activatedKeys.push(key);
          if (step.status === 'done' && c.from === step.agentId) activatedKeys.push(key);
        });

        if (activatedKeys.length) {
          setActiveConns((prev) => {
            const next = new Set(prev);
            activatedKeys.forEach((k) => next.add(k));
            return next;
          });
          const fade = setTimeout(() => {
            setActiveConns((prev) => {
              const next = new Set(prev);
              activatedKeys.forEach((k) => next.delete(k));
              return next;
            });
          }, 1400);
          timeoutsRef.current.push(fade);
        }

        if (idx === level.steps.length - 1) {
          const finalT = setTimeout(() => {
            setRunning(false);
            setCompleted(true);
            const lastDone = [...level.steps].reverse().find((s) => s.status === 'done' && s.output);
            if (lastDone) {
              const agent = level.agents.find((a) => a.id === lastDone.agentId);
              setFinalOutput({ agentName: agent?.name ?? lastDone.agentId, text: lastDone.output! });
            }
          }, 400);
          timeoutsRef.current.push(finalT);
        }
      }, cumulative);

      timeoutsRef.current.push(t);
    });
  }, [level, reset, running]);

  useEffect(() => () => clearAllTimeouts(), []);

  const connItems = level.connections.map((c, i) => ({ ...c, key: `${c.from}->${c.to}-${i}` }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Canvas */}
      <div style={{ position: 'relative', alignSelf: 'flex-start' }}>
        {/* Outer border — no overflow:hidden so tooltip can escape */}
        <div
          style={{
            width: CANVAS_W,
            height: CANVAS_H,
            background: 'var(--plate)',
            border: '1px solid var(--rule)',
            borderRadius: 2,
            position: 'relative',
          }}
        >
          {/* Grid plate — clipped separately */}
          <div
            ref={canvasRef}
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: 2,
              overflow: 'hidden',
              backgroundImage:
                'linear-gradient(to right, rgba(0,0,0,0.025) 1px, transparent 1px), linear-gradient(to bottom, rgba(0,0,0,0.025) 1px, transparent 1px)',
              backgroundSize: '24px 24px',
              pointerEvents: 'none',
            }}
          />

          {/* Corner crosshairs */}
          {[
            { style: { top: 10, left: 10, borderTop: '1px solid var(--ink-3)', borderLeft: '1px solid var(--ink-3)' } },
            { style: { top: 10, right: 10, borderTop: '1px solid var(--ink-3)', borderRight: '1px solid var(--ink-3)' } },
            { style: { bottom: 10, left: 10, borderBottom: '1px solid var(--ink-3)', borderLeft: '1px solid var(--ink-3)' } },
            { style: { bottom: 10, right: 10, borderBottom: '1px solid var(--ink-3)', borderRight: '1px solid var(--ink-3)' } },
          ].map((c, i) => (
            <div key={i} aria-hidden style={{ position: 'absolute', width: 12, height: 12, opacity: 0.45, ...c.style }} />
          ))}

          {/* Corner labels */}
          <div aria-hidden style={{ position: 'absolute', top: 12, left: 28, fontFamily: 'inherit', fontSize: 9.5, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'var(--ink-3)', opacity: 0.7 }}>
            LVL.{String(level.id).padStart(2, '0')}
          </div>
          <div aria-hidden style={{ position: 'absolute', bottom: 12, right: 28, fontFamily: 'inherit', fontSize: 9.5, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'var(--ink-3)', opacity: 0.7 }}>
            {level.agents.length} node{level.agents.length === 1 ? '' : 's'}
          </div>

          {/* SVG connections */}
          <svg
            style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 1 }}
            viewBox={`0 0 ${CANVAS_W} ${CANVAS_H}`}
            width={CANVAS_W}
            height={CANVAS_H}
          >
            <defs>
              <marker id="arrow-idle" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#C9C4B7" />
              </marker>
              <marker id="arrow-active" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--accent)" />
              </marker>
            </defs>

            {connItems.map((c) => {
              const from = level.agents.find((a) => a.id === c.from);
              const to = level.agents.find((a) => a.id === c.to);
              if (!from || !to) return null;
              const active = activeConns.has(c.key);
              const d = connectionPath(from, to);
              return (
                <g key={c.key}>
                  <path
                    d={d}
                    fill="none"
                    stroke={active ? 'var(--accent)' : '#C9C4B7'}
                    strokeWidth={active ? 1.6 : 1.25}
                    strokeDasharray={active ? undefined : '4 4'}
                    style={{ transition: 'stroke 180ms ease, stroke-width 180ms ease' }}
                    markerEnd={active ? 'url(#arrow-active)' : 'url(#arrow-idle)'}
                  />
                  {active && (
                    <path
                      d={d}
                      fill="none"
                      stroke="var(--accent)"
                      strokeWidth={2.2}
                      strokeDasharray="6 10"
                      strokeLinecap="round"
                      style={{ opacity: 0.85, animation: 'dashflow 0.9s linear infinite', filter: 'drop-shadow(0 0 4px rgba(204,102,51,0.25))' }}
                    />
                  )}
                </g>
              );
            })}
          </svg>

          {/* Agent nodes */}
          {level.agents.map((agent) => (
            <AgentNode
              key={agent.id}
              agent={agent}
              status={nodeStates[agent.id]?.status ?? 'idle'}
              output={nodeStates[agent.id]?.output}
              onHover={setHovered}
              onLeave={() => setHovered(null)}
              onClick={setClicked}
            />
          ))}

          {/* Hover tooltip */}
          {hovered && (
            <Tooltip
              agent={hovered}
              state={nodeStates[hovered.id]}
              canvasRef={canvasRef}
            />
          )}
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingTop: 4 }}>
        <button
          onClick={run}
          disabled={running || completed}
          style={{
            appearance: 'none',
            border: '1px solid var(--ink)',
            background: 'var(--ink)',
            color: 'var(--surface)',
            padding: '9px 16px',
            borderRadius: 2,
            fontSize: 13,
            letterSpacing: '0.01em',
            cursor: running || completed ? 'not-allowed' : 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            opacity: running || completed ? 0.55 : 1,
            transition: 'opacity 120ms ease, transform 100ms ease',
          }}
        >
          {running ? (
            <>
              <span style={{ width: 10, height: 10, borderRadius: '50%', border: '1.5px solid currentColor', borderRightColor: 'transparent', animation: 'spin 0.7s linear infinite', display: 'inline-block' }} />
              Running…
            </>
          ) : completed ? (
            'Demo complete'
          ) : (
            <>
              <span style={{ color: 'var(--accent)', fontSize: 11 }}>▸</span> Run demo
            </>
          )}
        </button>

        {(completed || running) && (
          <button
            onClick={reset}
            disabled={running}
            style={{
              appearance: 'none',
              background: 'transparent',
              border: '1px solid var(--ink-3)',
              color: 'var(--ink)',
              padding: '9px 16px',
              borderRadius: 2,
              fontSize: 13,
              cursor: running ? 'not-allowed' : 'pointer',
              opacity: running ? 0.55 : 1,
            }}
          >
            Reset
          </button>
        )}

        <div style={{ marginLeft: 8, fontSize: 11, color: 'var(--ink-3)', letterSpacing: '0.06em', fontFamily: 'inherit' }}>
          {running && `step ${currentStep + 1} of ${level.steps.length}`}
          {!running && completed && `finished — ${level.steps.length} steps`}
          {!running && !completed && 'idle — ready to dispatch'}
        </div>
      </div>

      {/* Final output */}
      {finalOutput && (
        <div style={{ border: '1px solid var(--rule)', borderRadius: 2, background: 'var(--surface)', overflow: 'hidden', animation: 'rise 320ms cubic-bezier(.2,.7,.2,1) both' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', padding: '12px 18px 10px', borderBottom: '1px solid var(--rule-2)', background: 'var(--plate)' }}>
            <span style={{ fontSize: 10.5, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--ink-3)' }}>
              Final output
            </span>
            <span style={{ fontSize: 12, color: 'var(--ink-2)' }}>
              returned by <strong style={{ fontWeight: 400, fontSize: 14, color: 'var(--ink)' }}>{finalOutput.agentName}</strong>
            </span>
          </div>
          <pre style={{ margin: 0, padding: '16px 20px 20px', fontFamily: 'inherit', fontSize: 12.5, lineHeight: 1.55, color: 'var(--ink)', whiteSpace: 'pre-wrap', maxHeight: 360, overflowY: 'auto' }}>
            {finalOutput.text}
          </pre>
        </div>
      )}

      {clicked && <NodeDetailModal agent={clicked} onClose={() => setClicked(null)} />}
    </div>
  );
}
