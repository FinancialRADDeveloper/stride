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

- The AI understands your codebase and project context, not just the snippet you've pasted.
- Your conventions and preferences are codified somewhere the AI can read them.
- You're making deliberate choices about which tasks go to AI and which stay with you.
- Sessions are structured so context accumulates rather than resets.

The goal is not to use AI more — it's to use it *better*. There's a meaningful difference.

---

## The Context Foundation: Specifications and Settings

To keep our AI assistants aligned across sessions, we maintain two primary context files at the root of the repo:

1. **project-settings.md:** Documents the project's identity, directory maps, code quality guidelines, and active tooling stacks.
2. **Stride - Python Spec.md:** The detailed technical architecture blueprint (SQLite schemas, append-only event log design, Pydantic models, and phase-by-phase build guidelines).

By keeping these files updated, any new agent (such as Google's Antigravity or Anthropic's Claude Code) can read them at the start of a session and immediately understand the project rules, target directories, and codebase boundaries without us having to re-explain the stack.

---

## Project Settings and Memory

Beyond spec files, there are a few other pieces of setup that make a meaningful difference.

**Project-level settings (`.claude/settings.json`)** let you configure tool permissions, define what the agent is allowed to do without asking, and configure project-specific behavior.

**Separate memory for reusable context** — some things belong in specifications and some belong in a decision log. I maintain a lightweight decisions log that captures the *why* behind significant choices—such as enforcing `PRAGMA journal_mode=DELETE` on SQLite for thread safety when bind-mounting volumes in Windows Docker containers. When an AI suggests a different approach, I can point it at the log rather than re-explaining the decision.

**Session notes** — at the end of each working session, I spend five minutes writing a brief note about where I left off, what I was in the middle of, and what the next step is. This takes thirty seconds to paste at the start of the next session and immediately orient the AI.

These aren't complicated systems. But they're the difference between an AI assistant that feels like it knows your project and one that feels like it's perpetually meeting you for the first time.

---

## What a Working Session Actually Looks Like

Here's the honest, unglamorous version of how a session goes:

**Starting up:** I open the repo, launch my terminal agent, and paste my session note from last time. This typically takes less than two minutes and it pays for itself within the first exchange.

**Planning before coding:** For anything non-trivial, I'll have a planning conversation before asking for code. What should this function do? What are the edge cases? Does this approach fit the existing patterns in the codebase? I've found that investing five minutes in this step saves much more time than it costs — the first draft of any code is dramatically better when the AI understands the intent properly.

**Code review as a habit:** I don't just accept AI output. I read it. I ask questions about choices I don't understand. I push back when something looks off. This sounds obvious but it's easy to slip into a pattern of accepting suggestions because they look right, and that's where AI-introduced bugs come from.

**Updating reference files:** If anything significant happened during the session — a decision made, a pattern established, a gotcha discovered — I update the spec files or project-settings before closing. Two minutes now, ten minutes saved in the next session.

It's not a dramatic process. It's just disciplined.

---

## How Antigravity, Claude Code, and Cursor Fit In

Claude Code does the initial scaffolding and scripting. Cursor comes in when I want visual IDE integration—working in files directly, seeing changes as a diff, and reviewing larger edits inline.

Google's **Antigravity** agent acts as our primary reasoning partner, performing complex refactors, verifying test files, managing git branch hygiene, and ensuring overall repository tidiness. 

By separating their roles, we avoid context-switching overhead and ensure we use the best tool for the job.

---

## The Lesson I'd Give Day-One Me

If I could go back to the moment I initialised this repo, I'd tell myself one thing: **the workflow is part of the product**.

The time you invest in your specifications, your conventions, your memory systems — that's not overhead. It's the foundation that makes everything else work. Developers who skip this end up fighting the AI instead of working with it. Every session restarts from zero. The assistant is capable but perpetually confused, which is exhausting for everyone.

Getting this right at the start is not a detour from the real work. It *is* the real work. After that, it quietly pays for itself every single session.

---

*Next up: I'll do a proper comparison of Antigravity, Claude Code, and Cursor — with real examples from Stride — so you can see how each one actually earns its place in a real project.*

---

### LinkedIn Share Blurb

Before writing a single line of feature code on my new project, I spent a full day setting up the AI-first workflow: specifications, project settings, session structure, and conventions that actually persist across sessions. It felt like overhead at the time. It absolutely was not. Second post in my building-with-AI series — this one's about the scaffolding that makes everything else work.

*[Link to post]*
