require("dotenv").config();
const express = require("express");
const OpenAI = require("openai");
const path = require("path");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const client = new OpenAI.default({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: "https://openrouter.ai/api/v1",
});

const MODEL = process.env.MODEL || "openai/gpt-4o-mini";

const SYSTEM_PROMPT = `You are a meeting notes summarizer. Given raw, messy meeting notes, extract and structure the key information.

Return ONLY valid JSON — no markdown, no explanation, just the JSON object — in this exact format:
{
  "summary": "A clear 2-4 sentence summary of what the meeting was about and what was covered.",
  "keyDecisions": [
    "Decision 1",
    "Decision 2"
  ],
  "actionItems": [
    { "task": "What needs to be done", "owner": "Name or null if not mentioned" }
  ]
}

Rules:
- If there are no key decisions, return an empty array for keyDecisions
- If there are no action items, return an empty array for actionItems
- If no owner is mentioned for an action item, set owner to null
- Keep the summary concise and jargon-free
- Infer action item owners from context (e.g. "John will set up the call" → owner: "John")`;

app.post("/api/summarize", async (req, res) => {
  const { notes } = req.body;

  if (!notes || notes.trim().length < 10) {
    return res.status(400).json({ error: "Please paste some meeting notes first." });
  }

  if (notes.length > 20000) {
    return res.status(400).json({ error: "Notes are too long. Please keep input under 20,000 characters." });
  }

  try {
    const response = await client.chat.completions.create({
      model: MODEL,
      max_tokens: 1024,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: `Here are my meeting notes:\n\n${notes}` },
      ],
    });

    const raw = response.choices[0].message.content.trim();
    const parsed = JSON.parse(raw);
    res.json(parsed);
  } catch (err) {
    if (err instanceof SyntaxError) {
      return res.status(500).json({ error: "Could not parse the AI response. Please try again." });
    }
    console.error(err);
    res.status(500).json({ error: "Something went wrong. Please try again." });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Meeting Notes Summarizer running at http://localhost:${PORT}`);
  console.log(`Model: ${MODEL}`);
});
