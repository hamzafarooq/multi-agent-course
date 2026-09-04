import MiniSearch from "minisearch";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

export type RagChunk = {
  id: string;
  source: string;
  heading: string;
  content: string;
};

let cached: { index: MiniSearch<RagChunk>; chunks: RagChunk[] } | null = null;

async function buildIndex() {
  const dir = path.join(process.cwd(), "corpus");
  const files = (await readdir(dir)).filter((f) => f.endsWith(".md"));

  const chunks: RagChunk[] = [];
  for (const file of files) {
    const text = await readFile(path.join(dir, file), "utf-8");
    const sections = text.split(/^##\s+/m);
    for (let i = 1; i < sections.length; i++) {
      const lines = sections[i].split("\n");
      const heading = (lines.shift() ?? "").trim();
      const content = lines.join("\n").trim();
      chunks.push({
        id: `${file}#${heading.toLowerCase().replace(/\s+/g, "-")}`,
        source: file,
        heading,
        content,
      });
    }
  }

  const index = new MiniSearch<RagChunk>({
    fields: ["heading", "content", "source"],
    storeFields: ["source", "heading", "content"],
    searchOptions: { fuzzy: 0.2, prefix: true, boost: { heading: 2 } },
  });
  index.addAll(chunks);

  return { index, chunks };
}

export async function ragSearch(query: string, limit = 3): Promise<RagChunk[]> {
  cached ??= await buildIndex();
  const hits = cached.index.search(query, { boost: { heading: 2 } }).slice(0, limit);
  return hits.map((h) => cached!.chunks.find((c) => c.id === h.id)!).filter(Boolean);
}
