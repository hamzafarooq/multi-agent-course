import { describe, it, expect } from "vitest";
import { buildStickies } from "./stickies";

describe("buildStickies", () => {
  describe("llm-only mode", () => {
    it("returns a single llm-only sticky regardless of inputs", () => {
      const stickies = buildStickies({ mode: "llm" });
      expect(stickies).toHaveLength(1);
      expect(stickies[0].kind).toBe("llm-only");
      expect(stickies[0].label).toMatch(/llm/i);
      expect(stickies[0].detail).toMatch(/training data/i);
    });
  });

  describe("tools mode", () => {
    it("emits a 'no tools needed' sticky when nothing fired", () => {
      const stickies = buildStickies({ mode: "tools", toolCalls: [] });
      expect(stickies).toHaveLength(1);
      expect(stickies[0].kind).toBe("llm-only");
      expect(stickies[0].label).toMatch(/no tool/i);
    });

    it("dedupes repeated tool calls into a single sticky with a count", () => {
      const stickies = buildStickies({
        mode: "tools",
        toolCalls: [
          { name: "rag_search", input: { query: "wispr" } },
          { name: "rag_search", input: { query: "krisp" } },
          { name: "rag_search", input: { query: "otter" } },
        ],
      });
      const rag = stickies.find((s) => s.label === "rag_search");
      expect(rag).toBeDefined();
      expect(rag!.kind).toBe("tool");
      expect(rag!.detail).toMatch(/3/);
    });

    it("emits separate stickies per distinct tool kind", () => {
      const stickies = buildStickies({
        mode: "tools",
        toolCalls: [
          { name: "rag_search", input: { query: "x" } },
          { name: "browser_navigate", input: { url: "https://example.com" } },
          { name: "browser_screenshot", input: {} },
        ],
      });
      const labels = stickies.map((s) => s.label).sort();
      expect(labels).toEqual(
        ["browser_navigate", "browser_screenshot", "rag_search"].sort(),
      );
    });

    it("includes the navigated URL in the browser_navigate sticky", () => {
      const stickies = buildStickies({
        mode: "tools",
        toolCalls: [
          { name: "browser_navigate", input: { url: "https://wisprflow.ai" } },
        ],
      });
      const nav = stickies.find((s) => s.label === "browser_navigate")!;
      expect(nav.detail).toContain("wisprflow.ai");
    });

    it("emits a web_search sticky when webSearchUsed is true", () => {
      const stickies = buildStickies({
        mode: "tools",
        toolCalls: [],
        webSearchUsed: true,
      });
      const web = stickies.find((s) => s.label === "web_search");
      expect(web).toBeDefined();
      expect(web!.kind).toBe("tool");
    });
  });

  describe("memory mode", () => {
    it("always includes CLAUDE.md and SKILL stickies even with no tool calls", () => {
      const stickies = buildStickies({ mode: "memory", toolCalls: [] });
      const kinds = stickies.map((s) => s.kind);
      expect(kinds).toContain("memory");
      expect(kinds).toContain("skill");
    });

    it("emits a remember sticky when remember_fact fired, with the saved fact in detail", () => {
      const stickies = buildStickies({
        mode: "memory",
        toolCalls: [
          { name: "remember_fact", input: { fact: "User targets enterprise legal teams." } },
        ],
      });
      const remember = stickies.find((s) => s.kind === "remember");
      expect(remember).toBeDefined();
      expect(remember!.detail).toContain("enterprise legal teams");
    });

    it("combines memory/skill stickies with tool stickies", () => {
      const stickies = buildStickies({
        mode: "memory",
        toolCalls: [
          { name: "rag_search", input: { query: "x" } },
          { name: "remember_fact", input: { fact: "B2B SaaS focus." } },
        ],
      });
      const kinds = stickies.map((s) => s.kind);
      expect(kinds).toContain("memory");
      expect(kinds).toContain("skill");
      expect(kinds).toContain("tool");
      expect(kinds).toContain("remember");
    });
  });

  describe("short-term mode", () => {
    it("returns a single short-term sticky regardless of inputs", () => {
      const stickies = buildStickies({ mode: "short-term" });
      expect(stickies).toHaveLength(1);
      expect(stickies[0].kind).toBe("short-term");
      expect(stickies[0].label).toMatch(/short-term/i);
      expect(stickies[0].detail).toMatch(/transcript|history/i);
    });
  });

  describe("long-term mode", () => {
    it("always includes the CLAUDE.md sticky, never SKILL or tool stickies", () => {
      const stickies = buildStickies({
        mode: "long-term",
        toolCalls: [{ name: "rag_search", input: { query: "x" } }],
      });
      const kinds = stickies.map((s) => s.kind);
      expect(kinds).toContain("memory");
      expect(kinds).not.toContain("skill");
      expect(kinds).not.toContain("tool");
    });

    it("emits a remember sticky when remember_fact fired, with the fact in detail", () => {
      const stickies = buildStickies({
        mode: "long-term",
        toolCalls: [
          { name: "remember_fact", input: { fact: "User researches Luma AI." } },
        ],
      });
      const remember = stickies.find((s) => s.kind === "remember");
      expect(remember).toBeDefined();
      expect(remember!.detail).toContain("Luma AI");
    });
  });
});
