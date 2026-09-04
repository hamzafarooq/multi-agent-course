export type RagChunk = {
  id: string;
  source: string;
  heading: string;
  content: string;
};

export async function ragSearch(_query: string, _limit = 3): Promise<RagChunk[]> {
  // TODO Exercise 2 (part 1) — implement keyword search over corpus/*.md
  // Suggested approach:
  // 1. Read all *.md files from corpus/
  // 2. Split each on "## " headings to make chunks
  // 3. Build a MiniSearch index over fields: heading, content, source
  // 4. Search with the query, return top `limit` chunks
  // Cache the index across calls so we don't rebuild on every query.
  return [];
}
