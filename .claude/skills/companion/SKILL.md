---
name: companion
description: Start or resume the FDE companion. Checks the student's setup (Git, the right folder), saves their name in fde-companion-kit/ME.md, and says which topic and step comes next. Use when the student types /companion or asks where they are in the companion or what to do next.
---

# /companion

0. **Read `fde-companion-kit/CLAUDE.md` first.** It is how you tutor for the companion, and it holds the topic table.

1. **Is this the first time?** Look for `fde-companion-kit/ME.md`.

2. **First time** (no `ME.md`):
   - Welcome them in two sentences: this repo is their workspace for the bootcamp and the companion, and you're their tutor. They watch and read on the site, and come back here for the hands-on steps.
   - **Check the setup**, saying what each check does before you run it:
     - Git: run `git --version`. If it's missing, tell them how to install it (Windows: Git for Windows from git-scm.com with the default options; Mac: VS Code or macOS offers to install it), then to close and reopen VS Code and type `/companion` again.
     - The folder: check that the open folder is `multi-agent-course` (it has `fde-companion-kit/` and `modules/` in it). If it isn't, ask them to choose **File › Open Folder** and pick `multi-agent-course`.
     - Claude Code: it's working, because you're answering.
   - Ask their **first name** and, in one line, **what they do** (for example "PM at a fintech" or "backend engineer").
   - Write `fde-companion-kit/ME.md`:

     ```markdown
     # Me
     Name: <first name>
     Role: <their one line>
     Started the companion: <today's date>
     ```

   - Tell them their setup is done: tick the last step of **Your FDE workbench** on the site, and move on to **1.1 What an FDE does** at https://companion.traversaal.ai/m0/what-an-fde-does/.

3. **Coming back** (`ME.md` exists): greet them by name. Progress lives on the site, not here, so ask which topic they're on (like 2.3). Then give the next hands-on step for that topic, from the table in `fde-companion-kit/CLAUDE.md`, and offer to start it. If the topic has nothing to do here, say so and point them to the next one that does. If they give an old number (like 1.2 or M04), map it with that file.

4. Keep the whole reply short. End with the one thing to do next.
