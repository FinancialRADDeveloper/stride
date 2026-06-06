# Why I Decided to Stop Shopping and Start Building

*The tools weren't broken. They just weren't mine.*

---

There's a particular kind of frustration that every developer knows. You have a clear picture of what you need. You open a browser tab, start comparing tools, read the docs, watch the demo videos, sign up for the free tier — and then sit with the uncomfortable realisation that nothing quite fits.

That was me, a few weeks ago.

I'd been looking for a tool to manage my rolling daily tasks and see ambient task histories (like how old a task is, and how many times I've moved it to "tomorrow" without doing it). I won't pretend the market is empty. There are plenty of options. The problem wasn't that nothing existed — it was that everything I tried was built around someone else's assumptions about how I work.

So I decided to build my own: **Stride**. And I decided to document the entire journey here.

---

## What I Actually Tried

I'm not going to name every tool I evaluated, but I'll be honest about what kept tripping me up.

Some tools were too opinionated. They'd made strong assumptions about workflow — the kind that made sense for a team of fifteen but felt like wearing a suit to write code when you're working solo. Every action required navigating through someone else's mental model of what a project looks like.

Others were too thin. Good ideas, weak execution. You'd get 80% of the way to useful and then hit a wall where the feature you needed just... wasn't there. With no obvious path to extending it yourself.

A few were genuinely impressive but solved a slightly different problem to mine. I'd find myself admiring the engineering and thinking "this is great — for someone else."

The common thread: none of them had been built with *my* specific use case in mind. Which is obvious in retrospect. Why would they be?

---

## The Moment the Decision Clicked

I was in the middle of yet another free trial when I caught myself spending more time configuring the tool than I would have spent just doing the thing manually. That's the tell. When the overhead of the solution exceeds the cost of the problem, something has gone wrong.

I closed the tab, opened a new one, and started writing notes about exactly what I actually wanted.

Within twenty minutes, I had a clearer picture of what Stride needed to do than any product page I'd read. The requirements weren't exotic — they were just specific to how I think and work. And the only way to get something built around how *I* think was to build it myself.

The slightly terrifying part: I'd have to actually build it.

---

## Why Now, Though?

Here's the honest answer: because this feels like the first moment in my career where building a solo project from scratch doesn't require me to compromise on pace or quality just because I'm working alone.

AI coding assistants have changed the economics of building. Not in a "AI writes all the code" way — I'd push back hard on that framing. But in a real, tangible way: the overhead of context-switching, of boilerplate, of remembering the exact API signature you used six weeks ago — a lot of that friction is gone. Or at least, significantly reduced.

I wanted to test that hypothesis properly. Not by reading about it, but by actually doing it.

---

## The Stack I'm Using

I'm not loyal to a single AI assistant. I've got three in rotation, and I think that's actually the right call:

**Antigravity** (Google DeepMind) — My primary reasoning and verification agent. When I'm rebasing code, verifying tests, tidying up directory structures, or designing complex multi-file integrations, Antigravity is the pairing partner I trust. Its systematic verification loops save hours of manual testing.

**Claude Code** — For bootstrapping and initial feature generation. It's excellent at generating scaffolding, drafting initial file specs, and writing markdown documentation.

**Cursor** — For anything that benefits from IDE-level visual integration. When I want to see the AI working *with* the code visually, side by side, or review a visual git diff, Cursor is where I go.

I'll write a dedicated post comparing these tools head-to-head — with real examples from this project. For now: I'm not trying to find one winner. Each has a different centre of gravity, and I want to understand where each one actually earns its place.

---

## What I'm Not Claiming

I want to be clear about something before this series goes any further.

I'm not claiming AI will write Stride for me. It won't. Every design decision, every architectural choice, every judgement call about what goes in version one versus what gets deferred — that's mine. The AI assists. The developer decides.

I'm also not claiming this will be faster or cheaper than hiring someone. I genuinely don't know yet. Part of what I'm trying to find out.

What I *am* claiming is that this is a genuinely interesting moment to be building something, and that documenting the reality of it — the wins, the frustrations, the bugs that AI introduced, the hours saved on boilerplate — is worth doing properly.

---

## What's Coming Next

In the next post, I'll walk through how I've structured my development environment from day one: the developer reference documentation, the project memory system, and what a working session actually looks like. Getting this right at the start has already paid dividends, and I think it's the piece most developers skip when they try to use AI coding assistants for real work.

If you're building something yourself, or seriously evaluating whether to, I hope this series gives you something more useful than a list of features. I'm going to tell you what it actually feels like — and what I'd do differently.

---

*Follow along on Hashnode, and if you're doing something similar, I'd genuinely love to hear about it in the comments.*

---

### LinkedIn Share Blurb

I spent weeks evaluating AI developer tools and realised none of them did exactly what I needed — so I decided to build my own from scratch, using Antigravity, Claude Code, and Cursor as my development stack. This is the first post in a series documenting the full journey: the decisions, the workflow, the mistakes, and what I'm learning. If you're curious about what AI-assisted development looks like on a real project, follow along.

*[Link to post]*
