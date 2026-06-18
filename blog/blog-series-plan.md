# Blog Series Plan: Building Stride — An AI-Assisted Developer Journey

**Series Title:** *From Prompt to Product: Building My Own AI-Powered Tool*

**Target Platform:** Hashnode
**Target Audience:** Developers curious about AI-assisted development, indie builders, tech leads evaluating AI tooling
**Posting Cadence:** Suggested every 1–2 weeks, aligned with actual build milestones
**Series Goal:** Document an honest, warts-and-all account of building a real tool using multiple AI coding assistants — establishing credibility as a practitioner, not just a commentator.

---

## Post 1: Why I Decided to Stop Shopping and Start Building

**Subtitle:** The tools weren't broken. They just weren't mine.

**Key Topics:**
- The itch that existing tools couldn't scratch (rolling daily lanes and ambient task history).
- A tour of what's already out there and where each fell short (anxiety-inducing backlogs, stateless swimlanes).
- The moment the decision clicked: build vs. buy.
- Introducing the AI assistant stack: Antigravity, Claude Code, and Cursor.
- What success looks like for Stride.

**LinkedIn Hook:** I spent weeks evaluating AI developer tools and realised none of them did exactly what I needed — so I decided to build my own, and document every step.

---

## Post 2: Setting Up an AI-First Development Workflow

**Subtitle:** Getting the scaffolding right before writing a single line of feature code.

**Key Topics:**
- What "AI-first" actually means in practice.
- Developer Reference: why `project-settings.md` and spec files matter for setting context.
- Conventions, memory systems, and keeping context across agent sessions.
- What a typical working session looks like with agent pairing.
- Lessons from day one of actually using this workflow.

**LinkedIn Hook:** Before writing a single line of feature code, I spent a day setting up my AI-first workflow — here's exactly how I structured it and why.

---

## Post 3: Choosing Your AI Assistants (And When to Switch)

**Subtitle:** Antigravity, Claude Code, and Cursor. Here's who bought the first round.

**Key Topics:**
- Honest comparison of Antigravity, Claude Code, and Cursor for different task types.
- When to reach for each tool: architecture vs. implementation vs. review.
- How to avoid context-switching overhead and maintain git branch hygiene.
- Building a mental model for which AI to ask what.
- Real examples from early Stride development.

**LinkedIn Hook:** I'm using multiple AI coding assistants on the same project — not because I couldn't pick one, but because each genuinely excels at different things.

---

## Post 4: My First Real Feature — Designed and Built with AI

**Subtitle:** From vague idea to working code, with an AI co-pilot for every step.

**Key Topics:**
- Walking through the full lifecycle of one feature: spec → design → code → review.
- How AI assistants changed (or didn't change) each phase.
- Where AI helped most and where it got in the way.
- Prompting strategies that actually worked.
- The feature itself: the horizontal day-lane board, capacity bars, and inline composer.

**LinkedIn Hook:** I just shipped my first real feature on Stride — here's an honest breakdown of how AI assisted (and occasionally hindered) every phase of the build.

---

## Post 5: When AI Gets It Wrong — Debugging With an AI Co-Pilot

**Subtitle:** AI-generated bugs are still bugs. Here's how to hunt them down together.

**Key Topics:**
- The bugs that AI introduced that I didn't catch immediately (category chip resetting, click propagation).
- Debugging strategies that work well with AI assistance.
- Teaching AI context about your codebase so it stops repeating mistakes.
- Updating developer references and project memory based on hard lessons.
- Why "trust but verify" is the right posture.

**LinkedIn Hook:** AI coding assistants introduced three bugs in one afternoon last week. Here's what I learned about debugging in an AI-first workflow — and how to make it not happen again.

---

## Post 6: Architecture Decisions I Made (and Let AI Challenge)

**Subtitle:** Using AI as a devil's advocate, not just a code generator.

**Key Topics:**
- Key architectural choices for Stride: what they were and why (SQLite stdlib connection, WAL mode, pure services).
- Using Claude Code and Cursor to pressure-test decisions before committing.
- When AI architectural suggestions were wrong (and why).
- Documenting decisions in a way AI can use later.
- The difference between AI-assisted thinking and AI-generated thinking.

**LinkedIn Hook:** The best thing about having an AI coding assistant isn't the code it writes — it's having something to argue with at 11pm when you're second-guessing a major architectural decision.

---

## Post 7: Tooling Hygiene: The Danger of "Vibe Coding" and Pivoting to Antigravity

**Subtitle:** Stripping out uv, avoiding tool creep, and switching AI developer agents mid-flight.

**Key Topics:**
- The trap of "vibe coding": letting tools and dependencies creep into a project without a deliberate learning session.
- Reverting from `uv` back to a clean `pip` + `requirements.txt` baseline.
- Designing for local-to-production parity: the path toward zero-configuration Dev Containers.
- Pivoting the agentic stack: introducing Google's Antigravity agent and establishing strict git/PR hygiene.

**LinkedIn Hook:** I stripped out a modern package manager and switched my primary AI agent mid-flight because I realized I was "vibe coding" instead of making deliberate engineering choices. Here's what I learned about tooling hygiene.

---

## Post 8: Testing Strategy in an AI-First Workflow

**Subtitle:** Who's responsible for quality when the AI wrote the code?

**Key Topics:**
- How AI changes (and doesn't change) your testing obligations.
- Getting AI to write useful tests — not just coverage padding.
- Review strategies: using one AI to review another's output.
- Building confidence in AI-generated code through systematic review.
- Current testing setup for Stride.

**LinkedIn Hook:** If an AI wrote the code and an AI wrote the tests, who's actually responsible for quality? Me. Here's how I think about testing in an AI-first workflow.

---

## Post 9: Shipping Something Real — The First Release

**Subtitle:** From private repo to actual users — what it took and what I learned.

**Key Topics:**
- What "done" looks like for v0.1 of Stride.
- The release checklist: what AI helped automate.
- First reactions: sharing with early users.
- What I'd do differently if I was starting again.
- The honest ROI of an AI-first development approach so far.

**LinkedIn Hook:** Stride just hit its first real release. Here's an honest retrospective on building with AI assistants from day one — what worked, what didn't, and what surprised me.

---

## Post 10: The Meta-Layer — How AI Is Changing How I Think as a Developer

**Subtitle:** Six months in, I think differently about problems. Here's how.

**Key Topics:**
- Cognitive shifts from sustained AI-assisted development.
- Skills that have improved vs. skills that have atrophied.
- What "developer judgment" means in 2026+.
- How I explain this workflow to colleagues who are skeptical.

**LinkedIn Hook:** After months of building with AI assistants every day, I've noticed it's changing how I think — not just how I code. Some of it surprises me.

---

## Post 11: What I'd Tell Someone Starting This Journey Today

**Subtitle:** Everything I wish I'd known before I typed the first prompt.

**Key Topics:**
- The single biggest mistake developers make with AI coding tools.
- The non-obvious setup steps that paid dividends.
- How to evaluate whether an AI suggestion is actually good.
- Building a sustainable AI-first practice, not a novelty-driven one.
- What's next for Stride and this series.

**LinkedIn Hook:** If you're thinking about building something serious with AI coding assistants, I've made the beginner mistakes so you don't have to. Here's what I'd tell myself starting over.

---

## Series Notes for the Author

- **Voice:** Keep it honest and specific. Readers trust concrete detail over vague enthusiasm. When something went wrong, say so — that's what builds credibility.
- **Code snippets:** Include real snippets where they add value, especially prompts that worked well. Readers love copy-paste prompts.
- **LinkedIn strategy:** Post each piece on LinkedIn with the hook line plus a genuine personal reflection. Tag relevant people (AI tool makers, developer advocates) where appropriate.
- **Cross-linking:** Each post should reference previous posts where relevant, and tease the next one at the end.
- **SEO titles to consider:** Phrases like "AI coding assistant comparison", "building with Cursor and Claude", "AI-first developer workflow", "vibe coding python".
