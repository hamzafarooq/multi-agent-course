---
name: companion
description: Start or resume the FDE companion. Checks the student's setup (Git, the right folder), saves their name in ME.md, and says which topic and step comes next. Use when the student types /companion or asks where they are or what to do next.
---

# /companion

1. **Is this the first time?** Look for `ME.md` in this folder.

2. **First time** (no `ME.md`):
   - Welcome them in two sentences: this folder is their workspace for the companion, and you're their tutor. They watch and read on the site, and come back here for the hands-on steps.
   - **Check the setup**, saying what each check does before you run it:
     - Git: run `git --version`. If it's missing, tell them how to install it (Windows: Git for Windows from git-scm.com with the default options; Mac: VS Code or macOS offers to install it), then to close and reopen VS Code and type `/companion` again.
     - The folder: check that the current folder is `fde-companion-kit`. If it isn't, ask them to choose **File › Open Folder** and pick `fde-companion-kit` inside the course folder.
     - Claude Code: it's working, because you're answering.
   - Ask their **first name** and, in one line, **what they do** (for example "PM at a fintech" or "backend engineer").
   - Write `ME.md`:

     ```markdown
     # Me
     Name: <first name>
     Role: <their one line>
     Started the companion: <today's date>
     ```

   - Tell them they're done with topic **0.2 Your FDE workbench**: tick the last step on the site, and move on to **0.3 How LLMs work** at https://fde-companion-pro.vercel.app/m0/how-llms-work/.

3. **Coming back** (`ME.md` exists): greet them by name. Progress lives on the site, not here, so ask which topic they're on (like 1.2). Then give the next hands-on step for that topic, from the table in `CLAUDE.md`, and offer to start it. If the topic has nothing to do here, say so and point them to the next one that does.

4. Keep the whole reply short. End with the one thing to do next.
