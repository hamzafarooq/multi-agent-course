"use client";

import { useState } from "react";

export default function Home() {
  const [notes, setNotes] = useState("");
  const [standup, setStandup] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    if (!notes.trim()) return;
    setLoading(true);
    setError("");
    setStandup("");

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Something went wrong");
      } else {
        setStandup(data.standup);
      }
    } catch {
      setError("Failed to reach the server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "60px auto", padding: "0 20px", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>MeetingMemo</h1>
      <p style={{ color: "#666", marginBottom: 32 }}>
        Paste raw meeting notes → get a clean standup update
      </p>

      <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
        Meeting notes
      </label>
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Paste your meeting notes here..."
        rows={10}
        style={{
          width: "100%",
          padding: "12px 14px",
          fontSize: 14,
          border: "1px solid #ddd",
          borderRadius: 8,
          resize: "vertical",
          fontFamily: "inherit",
          boxSizing: "border-box",
        }}
      />

      <button
        onClick={generate}
        disabled={loading || !notes.trim()}
        style={{
          marginTop: 12,
          padding: "10px 24px",
          background: loading ? "#999" : "#E03030",
          color: "#fff",
          border: "none",
          borderRadius: 6,
          fontWeight: 600,
          fontSize: 14,
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "Generating..." : "Generate Standup"}
      </button>

      {error && (
        <p style={{ marginTop: 16, color: "#c00", fontWeight: 500 }}>{error}</p>
      )}

      {standup && (
        <div style={{ marginTop: 32 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Standup update</h2>
          <div
            style={{
              background: "#f7f7f7",
              border: "1px solid #e8e8e8",
              borderRadius: 8,
              padding: "16px 20px",
              fontSize: 14,
              lineHeight: 1.7,
              whiteSpace: "pre-wrap",
            }}
          >
            {standup}
          </div>
          <button
            onClick={() => navigator.clipboard.writeText(standup)}
            style={{
              marginTop: 10,
              padding: "6px 16px",
              background: "transparent",
              border: "1px solid #ddd",
              borderRadius: 6,
              fontSize: 13,
              cursor: "pointer",
              color: "#444",
            }}
          >
            Copy to clipboard
          </button>
        </div>
      )}
    </main>
  );
}
