---
name: prework
description: Start or resume the FDE pre-work. Checks the student's setup (Git, the right folder), saves their name in ME.md, and says which module and step comes next. Use when the student types /prework or asks where they are or what to do next.
---

# /prework

1. **Is this the first time?** Look for `ME.md` in this folder.

2. **First time** (no `ME.md`):
   - Welcome them in two sentences: this folder is their pre-work workspace, and you're their tutor. They watch and read on the site, and come back here for the hands-on steps.
   - **Check the setup**, saying what each check does before you run it:
     - Git: run `git --version`. If it's missing, tell them how to install it (Windows: Git for Windows from git-scm.com with the default options; Mac: VS Code or macOS offers to install it), then to close and reopen VS Code and type `/prework` again.
     - The folder: check that the current folder is `fde-starter-kit`. If it isn't, ask them to choose **File › Open Folder** and pick `fde-starter-kit` inside the course folder.
     - Claude Code: it's working, because you're answering.
   - Ask their **first name** and, in one line, **what they do** (for example "PM at a fintech" or "backend engineer").
   - Write `ME.md`:

     ```markdown
     # Me
     Name: <first name>
     Role: <their one line>
     Started the pre-work: <today's date>
     ```

   - Tell them they're done with Module 1: tick the last step on the site, and move on to **Module 2 · How LLMs work** at https://fde-starter.vercel.app/module/m02/.

3. **Coming back** (`ME.md` exists): greet them by name. Progress lives on the site, not here, so ask which module they're on. Then give the next hands-on step for that module, from the table in `CLAUDE.md`, and offer to start it.

4. Keep the whole reply short. End with the one thing to do next.
