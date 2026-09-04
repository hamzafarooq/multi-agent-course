import { describe, it, expect } from "vitest";
import { ragSearch } from "./rag";

describe("ragSearch", () => {
  it("returns chunks from the wispr flow doc for a Wispr Flow query", async () => {
    const results = await ragSearch("Wispr Flow pricing");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].source).toMatch(/wispr-flow/);
  });

  it("returns chunks from multiple sources for a generic competitor query", async () => {
    const results = await ragSearch("competitor pricing");
    const sources = new Set(results.map((r) => r.source));
    expect(sources.size).toBeGreaterThan(1);
  });

  it("returns the open-source brief for a license query", async () => {
    const results = await ragSearch("open source GPL");
    expect(results.some((r) => r.source.includes("voiceink"))).toBe(true);
  });
});
