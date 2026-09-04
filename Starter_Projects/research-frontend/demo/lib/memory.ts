import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const FILE = path.join(process.cwd(), "memory/CLAUDE.md");
const SKILL = path.join(process.cwd(), "skills/research/SKILL.md");
const FACTS_MARKER = "## Known facts";

export async function readMemory(): Promise<string> {
  return await readFile(FILE, "utf-8");
}

export async function readSkill(): Promise<string> {
  return await readFile(SKILL, "utf-8");
}

export async function appendFact(fact: string): Promise<void> {
  const cleaned = fact.trim().replace(/^[-*]\s*/, "");
  const current = await readFile(FILE, "utf-8");
  const idx = current.indexOf(FACTS_MARKER);
  if (idx === -1) {
    await writeFile(FILE, `${current.trimEnd()}\n\n- ${cleaned}\n`, "utf-8");
    return;
  }
  const before = current.slice(0, idx + FACTS_MARKER.length);
  const after = current.slice(idx + FACTS_MARKER.length);
  const newAfter = after.replace(/_\(this section grows over the conversation\)_\s*/g, "");
  const updated = `${before}\n\n- ${cleaned}${newAfter.startsWith("\n") ? "" : "\n"}${newAfter}`;
  await writeFile(FILE, updated, "utf-8");
}
