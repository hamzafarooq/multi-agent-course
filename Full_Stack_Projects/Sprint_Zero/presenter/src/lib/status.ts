import { useEffect, useRef, useState } from "react";
import type { Status } from "./types";

const EMPTY_STATUS: Status = {
  phase: "idle",
  docs: [],
};

let demoMode = false;
export function isDemoMode() {
  return demoMode;
}

export function useStatus(demo = false): Status {
  const [status, setStatus] = useState<Status>(EMPTY_STATUS);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let cancelled = false;
    demoMode = demo;

    if (demo) {
      fetch("/api/sample/state")
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error("no sample"))))
        .then((data) => {
          if (!cancelled) setStatus({ ...data, demo: true });
        })
        .catch(() => {
          if (!cancelled) setStatus({ ...EMPTY_STATUS, demo: true });
        });
      return () => {
        cancelled = true;
      };
    }

    // Hydrate from the server, then open SSE stream.
    fetch("/api/state")
      .then((r) => r.json())
      .then((data) => {
        if (!cancelled) setStatus(data);
      })
      .catch(() => {
        /* server may not be up in dev with only the vite side — tolerate. */
      });

    const es = new EventSource("/api/stream");
    esRef.current = es;

    es.addEventListener("status", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        setStatus(data);
      } catch {
        /* ignore */
      }
    });

    return () => {
      cancelled = true;
      es.close();
    };
  }, [demo]);

  return status;
}

export async function submitScope(payload: unknown): Promise<{ ok: boolean; error?: string }> {
  try {
    const r = await fetch("/api/scope", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      const text = await r.text();
      return { ok: false, error: text || `HTTP ${r.status}` };
    }
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : "Network error" };
  }
}

export async function fetchDoc(name: string): Promise<string> {
  const base = demoMode ? "/api/sample/doc" : "/api/doc";
  const r = await fetch(`${base}/${encodeURIComponent(name)}`);
  if (!r.ok) throw new Error(`Could not load ${name}`);
  return r.text();
}
