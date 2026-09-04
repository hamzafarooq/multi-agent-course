import { afterEach, describe, it, expect } from "vitest";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { readMemory, appendFact } from "./memory";

const FILE = path.join(process.cwd(), "memory/CLAUDE.md");

let backup: string;

describe("memory", () => {
  afterEach(async () => {
    if (backup !== undefined) await writeFile(FILE, backup, "utf-8");
  });

  it("readMemory returns the file contents", async () => {
    backup = await readFile(FILE, "utf-8");
    const text = await readMemory();
    expect(text).toContain("User context");
  });

  it("appendFact adds a bullet to Known facts", async () => {
    backup = await readFile(FILE, "utf-8");
    await appendFact("the user is exploring the agent-voice-interface angle");
    const updated = await readFile(FILE, "utf-8");
    expect(updated).toMatch(/- the user is exploring the agent-voice-interface angle/);
  });
});
