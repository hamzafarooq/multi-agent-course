import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

export async function POST(req: Request) {
  try {
    const { notes } = await req.json();

    if (!notes || notes.trim().length === 0) {
      return Response.json({ error: "No meeting notes provided" }, { status: 400 });
    }

    const message = await client.messages.create({
      model: "claude-opus-4-7",
      max_tokens: 1024,
      system: `You convert raw meeting notes into a structured standup update.

Always return exactly three sections with these exact headings:

## What we decided
[bullet points — key decisions made in the meeting]

## What I'm doing next
[bullet points — action items, include owner names if mentioned]

## What's blocked
[bullet points — open blockers or questions; write "Nothing blocked" if none]

Be concise. One bullet per item. No preamble, no summary, no closing remarks.`,
      messages: [{ role: "user", content: notes }],
    });

    const text =
      message.content[0].type === "text" ? message.content[0].text : "";

    return Response.json({ standup: text });
  } catch (error) {
    console.error("Claude API error:", error);
    return Response.json({ error: "Failed to generate standup" }, { status: 500 });
  }
}
