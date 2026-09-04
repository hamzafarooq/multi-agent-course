import { describe, it, expect } from "vitest";
import { executeToolUse } from "./tool-loop";

describe("executeToolUse", () => {
  it("routes rag_search calls to ragSearch", async () => {
    const result = await executeToolUse({
      name: "rag_search",
      input: { query: "Wispr Flow" },
    });
    expect(typeof result.text).toBe("string");
    expect(result.text.toLowerCase()).toContain("wispr");
    expect(result.imageBase64).toBeUndefined();
  });

  it("returns an error string for unknown tools instead of throwing", async () => {
    const result = await executeToolUse({
      name: "nonexistent_tool",
      input: {},
    });
    expect(result.text).toMatch(/unknown/i);
  });
});
