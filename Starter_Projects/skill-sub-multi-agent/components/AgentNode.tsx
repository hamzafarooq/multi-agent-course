'use client';

import { AgentDef, AgentStatus } from '@/lib/demo-data';

const NODE_W = 170;
const NODE_H = 78;

interface Props {
  agent: AgentDef;
  status: AgentStatus;
  output?: string;
  onHover: (agent: AgentDef) => void;
  onLeave: () => void;
  onClick: (agent: AgentDef) => void;
}

export { NODE_W, NODE_H };

export default function AgentNode({ agent, status, output, onHover, onLeave, onClick }: Props) {
  const isThinking = status === 'thinking';
  const isDone = status === 'done';

  const borderColor = isThinking
    ? 'var(--accent)'
    : isDone
    ? 'var(--done)'
    : 'var(--rule)';

  const boxShadow = isThinking
    ? '0 0 0 4px var(--accent-2), 0 1px 0 rgba(0,0,0,0.04)'
    : isDone
    ? '0 0 0 4px var(--done-2)'
    : '0 1px 0 rgba(0,0,0,0.02)';

  const bg =
    agent.role === 'human' ? '#F4F1EC' :
    agent.role === 'orch' || agent.role === 'merge' ? '#FFF' : 'var(--surface)';

  return (
    <div
      onMouseEnter={() => onHover(agent)}
      onMouseLeave={onLeave}
      onClick={() => onClick(agent)}
      style={{
        position: 'absolute',
        left: agent.x,
        top: agent.y,
        width: NODE_W,
        height: NODE_H,
        background: bg,
        border: `1px solid ${borderColor}`,
        borderRadius: 3,
        padding: '10px 12px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxShadow,
        transition: 'border-color 200ms ease, box-shadow 200ms ease, background 200ms ease',
        zIndex: 2,
        cursor: 'help',
      }}
    >
      {/* Status row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 4 }}>
        <span
          style={{
            position: 'relative',
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: isThinking
              ? 'var(--accent)'
              : isDone
              ? 'var(--done)'
              : 'var(--ink-3)',
            flexShrink: 0,
          }}
        >
          {isThinking && (
            <span
              style={{
                position: 'absolute',
                inset: -4,
                borderRadius: '50%',
                border: '1px solid var(--accent)',
                animation: 'agentpulse 1.2s ease-out infinite',
                opacity: 0.6,
              }}
            />
          )}
        </span>
        <span
          style={{
            fontFamily: 'inherit',
            fontSize: 9.5,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: isThinking ? 'var(--accent)' : isDone ? 'var(--done)' : 'var(--ink-3)',
          }}
        >
          {status === 'idle' && 'idle'}
          {status === 'thinking' && 'thinking…'}
          {status === 'done' && (output ? 'done' : 'ready')}
        </span>
      </div>

      {/* Agent name */}
      <div
        style={{
          fontSize: 17,
          lineHeight: 1.1,
          color: 'var(--ink)',
          letterSpacing: '-0.005em',
          fontWeight: 400,
          overflow: 'hidden',
          whiteSpace: 'nowrap',
          textOverflow: 'ellipsis',
        }}
      >
        {agent.name}
      </div>

      {/* Sublabel */}
      {agent.sublabel && (
        <div
          style={{
            fontSize: 9.5,
            color: 'var(--ink-3)',
            letterSpacing: '0.08em',
            marginTop: 2,
            overflow: 'hidden',
            whiteSpace: 'nowrap',
            textOverflow: 'ellipsis',
          }}
        >
          {agent.sublabel}
        </div>
      )}
    </div>
  );
}
