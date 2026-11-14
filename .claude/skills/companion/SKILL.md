---
name: companion
description: The student's front door to the FDE Bootcamp. Checks their setup, gives a short tour of this repo, says what to do next, and answers any question about the course or where something is in the repo, with the exact files. Use when the student types /companion (with or without a question), asks where to start, where something is, what to do next, or how the repo works.
argument-hint: "[question about the course or the repo]"
---

# /companion

The student typed: `$ARGUMENTS`

0. **Read `fde-companion-kit/CLAUDE.md` first.** It is how you tutor here, and it holds the repo map and the topic table.

1. **Is this the first time?** Look for `fde-companion-kit/ME.md`. If it's missing, do step 2 first, even if they asked a question (then answer it).

2. **First time** (no `ME.md`):
   - Welcome them in two sentences: this repo is everything they need for the bootcamp, and you're their guide to it. They watch and read on the companion site, and work here.
   - **Check the setup**, saying what each check does before you run it:
     - Git: run `git --version`. If it's missing, tell them how to install it (Windows: Git for Windows from git-scm.com with the default options; Mac: VS Code or macOS offers to install it), then to close and reopen VS Code and type `/companion` again.
     - The folder: check that the open folder is `multi-agent-course` (it has `fde-companion-kit/` and `modules/` in it). If it isn't, ask them to choose **File › Open Folder** and pick `multi-agent-course`.
     - Up to date: run `git pull` and say in one line what came in. The repo changes during the course.
     - Claude Code: it's working, because you're answering.
   - Ask their **first name** and, in one line, **what they do** (for example "PM at a fintech" or "backend engineer").
   - Write `fde-companion-kit/ME.md`:

     ```markdown
     # Me
     Name: <first name>
     Role: <their one line>
     Started the companion: <today's date>
     ```

   - **The tour:** the five places in the repo map ("Where things are") in `fde-companion-kit/CLAUDE.md`, one line each, as links. Shape the last line to their role: a PM or founder starts with a starter project, an engineer can go straight to the current project.
   - Tell them their setup is done: tick the last step of **Your FDE workbench** on the site, and move on to **1.1 What an FDE does** at https://companion.traversaal.ai/m0/what-an-fde-does/.

3. **A question** (`$ARGUMENTS` isn't empty): answer it from the repo, using "Answering questions" in `fde-companion-kit/CLAUDE.md`.

4. **Coming back, no question** (`ME.md` exists): greet them by name and run `git pull` (say what came in, if anything). Ask which of these they want:
   - **Next companion step:** progress lives on the site, so ask which topic they're on (like 2.3) and give that topic's hands-on step from the topic table. If it has nothing to do here, point them to the next one that does.
   - **Their project:** find the current one in the repo map, and start them with `START_HERE.md`.
   - **Learn a module** with the course tutor: tell them to type `/start`.
   - **Find something:** ask what they're looking for.

5. Keep the whole reply short. End with the one thing to do next.
