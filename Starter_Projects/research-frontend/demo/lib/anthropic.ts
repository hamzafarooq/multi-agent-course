import Anthropic from "@anthropic-ai/sdk";

export const MODEL = "claude-sonnet-4-6";

// Build a client per request. A user-supplied key (entered in the UI) wins;
// otherwise fall back to the server's ANTHROPIC_API_KEY env var.
export function getAnthropic(apiKey?: string) {
  const key = apiKey?.trim() || process.env.ANTHROPIC_API_KEY;
  if (!key) {
    throw new Error(
      "No Anthropic API key. Enter your key in the field at the top of the page, or set ANTHROPIC_API_KEY on the server.",
    );
  }
  return new Anthropic({ apiKey: key });
}
