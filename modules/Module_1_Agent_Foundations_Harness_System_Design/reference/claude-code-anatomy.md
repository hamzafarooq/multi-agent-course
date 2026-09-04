# Reference — The Claude Code Ecosystem

<!-- INSTRUCTOR: Background for modules that cover the Claude harness and its constructs. -->

## The harness, layered
Harness → Context management → Agent loop → (Tools · Memory · Permissions) → LLM ("the brain").
**The model thinks. The harness does.**

## The five constructs
1. **CLAUDE.md** — Project memory; loaded every session; lives in the root.
2. **Skills** — Reusable instruction packs (SKILL.md + assets), auto-invoked by description.
3. **MCP servers** — Tool extensions (GitHub, Slack, Figma, DBs…). Flow: Claude → MCP server
   → tool → result → Claude.
4. **Subagents** — Parallel delegates with isolated context, own prompt/tools/model.
5. **Hooks** — Deterministic automations on events. Prompts *suggest* (~95%); hooks *enforce*
   (100%). If a failure causes real-world harm, build a hook.

## Skills vs. subagents vs. main agent
- **Main agent** — shared, monolithic context; orchestrator; your terminal session.
- **Subagent** — 100% isolated context, spawned fresh and discarded; focused background work.
- **Skill** — injected on demand into the active window; reusable knowledge, cross-platform.
