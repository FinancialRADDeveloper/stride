# Setting Up an AI-First Development Workflow

*Getting the scaffolding right before writing a single line of feature code.*

---

The temptation, when you start a new project, is to start coding.

I know this feeling well. You've made the decision, you're excited, the blank repo is right there — and the most satisfying thing in the world is to start filling it with something that looks like progress. A folder structure. An initial commit. Maybe a `README.md` that describes the project you're going to build as if it already exists.

I did something different this time. Before I wrote a single line of feature code, I spent a full day setting up the workflow itself. The conventions, the configuration, the prompting patterns, the memory systems. The scaffolding that would make AI actually useful for sustained work rather than just impressive for the first hour.

It was one of the better decisions I've made on this project.

---

## What "AI-First" Actually Means

There's a version of "AI-assisted development" that looks like this: you write code, you get stuck, you paste a question into ChatGPT, you take the answer, you carry on. That's fine. It's useful. But it's not what I'm doing here.

An AI-first workflow is something different. It means:

- The AI understands your codebase and project context, not just the snippet you've pasted
- Your conventions and preferences are codified somewhere the AI can read them
- You're making deliberate choices about which tasks go to AI and which stay with you
- Sessions are structured so context accumulates rather than resets

The goal is not to use AI more — it's to use it *better*. There's a meaningful difference.

---

## The Most Important File in My Repo: CLAUDE.md

If you're using Claude Code and you haven't set up a `CLAUDE.md` file, stop reading this and go do that first.

`CLAUDE.md` is a markdown file that Claude Code reads at the start of every session. Think of it as the briefing document you'd give to a new contractor on their first day. It tells the AI:

- What this project is and what problem it solves
- The tech stack, directory structure, and key dependencies
- Conventions to follow (naming patterns, file organisation, preferred patterns)
- Things to avoid (anti-patterns you've already decided against, approaches that don't fit this codebase)
- Current project status and what's in progress

Here's what mine covers, roughly:

```markdown
# [TOOL NAME] — Developer Reference

## Project Overview
[What the tool does and why it exists]

## Stack
- [Language/runtime]
- [Key frameworks and libraries]
- [Build tooling]

## Directory Structure
[Brief map of the top-level folders and what lives where]

## Conventions
- [Naming conventions for files, functions, variables]
- [How to handle errors]
- [Where config lives]
- [Testing approach]

## Current Status
- What's built and working
- What's in progress
- What's explicitly deferred to later

## Things to Remember
- [Decisions made and why — saves re-litigating them mid-session]
- [Gotchas discovered through experience]
```

This file evolves. Every time I make a significant architectural decision, or discover something surprising about the codebase, I update it. The discipline of updating it regularly is almost as valuable as having it in the first place — it forces you to articulate decisions clearly rather than leaving them as vague intentions.

---

## Project Settings and Memory

Beyond `CLAUDE.md`, there are a few other pieces of setup that make a meaningful difference.

**Project-level settings (`.claude/settings.json`)** let you configure tool permissions, define what Claude Code is allowed to do without asking, and set up any project-specific behaviour. I've used this to allow the file operations and shell commands I know I'll need repeatedly, so I'm not approving them one by one.

**Separate memory for reusable context** — some things belong in CLAUDE.md and some belong elsewhere. I maintain a lightweight decisions log (just a markdown file committed to the repo) that captures the *why* behind significant choices. Not the code — the reasoning. When AI suggests an approach I've already considered and rejected, I can point it at the decisions log rather than re-explaining it each time.

**Session notes** — at the end of each working session, I spend five minutes writing a brief note about where I left off, what I was in the middle of, and what the next step is. This takes thirty seconds to paste at the start of the next session and immediately orients the AI without me having to reconstruct the context from scratch.

These aren't complicated systems. But they're the difference between an AI assistant that feels like it knows your project and one that feels like it's perpetually meeting you for the first time.

---

## What a Working Session Actually Looks Like

Here's the honest, unglamorous version of how a session goes:

**Starting up:** I open the repo, launch Claude Code, and paste my session note from last time. Sometimes I also paste a quick summary of what I want to accomplish today. This typically takes less than two minutes and it pays for itself within the first exchange.

**Planning before coding:** For anything non-trivial, I'll have a planning conversation before asking for code. What should this function do? What are the edge cases? Does this approach fit the existing patterns in the codebase? I've found that investing five minutes in this step saves much more time than it costs — the first draft of any code is dramatically better when the AI understands the intent properly.

**Code review as a habit:** I don't just accept AI output. I read it. I ask questions about choices I don't understand. I push back when something looks off. This sounds obvious but it's easy to slip into a pattern of accepting suggestions because they look right, and that's where AI-introduced bugs come from.

**Updating CLAUDE.md:** If anything significant happened during the session — a decision made, a pattern established, a gotcha discovered — I update CLAUDE.md before closing. Two minutes now, ten minutes saved in the next session.

It's not a dramatic process. It's just disciplined.

---

## What Cursor, Codex, and Junie Fit In

For now, Claude Code is doing the heavy lifting. It's where I spend most of my development time and where the CLAUDE.md setup makes the biggest difference.

Cursor comes in when I want the visual integration — working in files directly, seeing changes as a diff, reviewing larger edits inline. I'll write more about the distinction in a future post, but broadly: Claude Code for driving, Cursor for reviewing and refactoring.

Codex and Junie [describe your current usage here — e.g. "are currently in reserve for specific task types I'll cover as they come up"]. I'll write a dedicated post comparing all four once I have more meaningful data from real project work.

---

## The Lesson I'd Give Day-One Me

If I could go back to the moment I initialised this repo, I'd tell myself one thing: **the workflow is part of the product**.

The time you invest in your CLAUDE.md, your conventions, your memory systems — that's not overhead. It's the foundation that makes everything else work. Developers who skip this end up fighting the AI instead of working with it. Every session restarts from zero. Every piece of context has to be re-established. The assistant is capable but perpetually confused, which is exhausting for everyone.

Getting this right at the start is not a detour from the real work. It *is* the real work, for the first day or two. After that, it quietly pays for itself every single session.

---

*Next up: I'll do a proper comparison of Claude Code, Cursor, Codex, and Junie — with real examples from [TOOL NAME] — so you can see how each one actually earns its place in a real project.*

---

### LinkedIn Share Blurb

Before writing a single line of feature code on my new project, I spent a full day setting up the AI-first workflow: CLAUDE.md, project memory, session structure, and conventions that actually persist across sessions. It felt like overhead at the time. It absolutely was not. Second post in my building-with-AI series — this one's about the scaffolding that makes everything else work.

*[Link to post]*
