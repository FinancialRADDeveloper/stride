# My First Real Feature — Designed and Built with AI

*From vague idea to working code, with a detour through a toy that changed everything.*

---

Before I wrote a single line of Python for Stride, I had a working application in my browser.

Not a real one. A toy. Hardcoded dates, fake tasks, no database, no persistence. Click a button and nothing is actually saved anywhere. But it looked right, it felt right, and when I dragged a card from Tuesday to Wednesday the board behaved exactly the way I had in my head.

That toy — a prototype built entirely with Claude Design before the Python project even existed — turned out to be the most important thing I did in this whole build. Here's why.

---

## What I Actually Wanted

The requirements weren't exotic. I wanted a day-lane task board, roughly in the spirit of Todoist or a stripped-down Jira, but with something neither of those does well: **honest history tracking**.

Every card needed to carry its own record. How old is it? How many times has it been pushed forward to another day? How many times has its title changed? I've seen tasks sit in a backlog for two weeks because every time they show up, you just slide them to tomorrow — and nothing about the card tells you that's been happening. I wanted cards that told the truth about themselves.

Alongside that: a Google Calendar sync with real sub-calendar support (not just "push to primary"), and a way to mark some tasks as Personal and others as Shared, targeting different calendars automatically.

Clear enough to describe. Vague enough that I genuinely didn't know what the UI should look like until I'd tried it.

---

## Enter Claude Design

Claude Design is Claude's visual prototyping tool. You describe what you want, and it builds a functional, interactive mockup — React components you can actually click on in the browser.

I described Stride. What came back was five React/JSX files (`app.jsx`, `card.jsx`, `detail.jsx`, `tweaks-panel.jsx`, `util.jsx`) and a single self-contained `Stride.html` file with realistic seed data baked in.

Here's what the prototype actually does:

**The board** shows six days in a rolling window — yesterday through four days ahead. Each column has a capacity bar that fills based on task estimates, so you can see at a glance when you're overloading a day. Cards show their category as a colored left border, their priority and size labels, and a small stale ribbon on any card that's been moved three or more times. The board is filterable by category — click a pill in the legend strip and everything else dims.

**Card detail** opens as a right-side panel. Priority, size, estimate, target time — all editable inline. The calendar chooser mirrors Google Calendar's sidebar: accounts listed with their sub-calendars underneath, each with a colored checkbox. You can set the global "Personal" or "Shared" target calendar, or override per card. Below the fields, a full activity timeline: created, moved from Monday to Tuesday, title changed from X to Y, marked done, reopened — every event with a timestamp. Underneath that, counters: age in days, move count, edit count.

**The tweaks panel** (a collapsible sidebar) lets you adjust board settings live: show/hide completed tasks, toggle the category legend, change the staleness threshold.

It's all hardcoded. The date is fixed. The tasks don't move between sessions. It has the structural integrity of a cardboard mockup — which is exactly the right structural integrity for this stage.

---

## The Honest Limitations

Let me be clear about what the prototype is not.

It's not a product. It's not even a prototype in the "we'll iterate on this" sense. It's a frozen design artefact. Its job was to answer one question: **does this UI make sense?**

The seed data is fictional. The categories are made up. The calendar accounts aren't connected to anything. The drag-and-drop works in the browser but doesn't call any backend because there is no backend. The activity timeline shows hand-crafted events that don't correspond to any real history.

Any serious use of this thing would immediately expose all of that. But that's fine. That's its job done. When I look at the prototype and everything feels right — the capacity bars are useful, the stale ribbon is doing work, the calendar chooser is laid out in a way that makes the sub-calendar selection obvious — then the prototype has succeeded. When something feels off, I go back to Claude Design and change it before I've written a single callback.

The Python application is where the real design work happens. The prototype is just proof that the real design is worth building.

---

## Why Designing Before Coding Is Different With AI

You might be thinking: designers have always built prototypes before writing production code. This isn't new. And you're right — the principle isn't new. But the economics have changed.

Before AI-assisted prototyping, the realistic options for a solo developer were: sketch it on paper (fast but not interactive), build it in Figma (interactive but disconnected from code), or just start building and accept that your initial UI decisions might be wrong (which is what most of us actually did).

With Claude Design, I described what I wanted in a long conversation, gave feedback on a first pass, asked for specific changes, and ended up with a fully interactive HTML file that I could sit with for an afternoon. The time between "I have an idea" and "I have something I can actually click on" collapsed dramatically.

Here's why that matters more than it sounds.

When I eventually opened Claude Code and started the Python build, I wasn't **exploring**. I was **implementing**. Those are completely different cognitive states, and they have completely different relationships with an AI coding assistant.

When you're exploring, you're changing your mind constantly — about what the UI needs, about what data the backend needs to provide, about what "done" even means. AI coding assistants are genuinely less useful in that mode, because you keep changing direction and the AI keeps doing work that turns out to be wrong. You spend half your time correcting course.

When you're implementing a known shape, the AI is excellent. You give it a spec, it builds, you review. The spec for Stride's Python build is a detailed document (`Stride - Python Spec.md`) that references the prototype as the visual and interaction source of truth. Any ambiguity about how something should look or behave gets resolved by looking at `Stride.html`. The prototype is the tiebreaker.

The sentence I keep coming back to: **the mockup is a frozen spec that can't be misread.** You can misread a written requirements document. You can misread a Figma file if you're not sure how transitions should behave. You cannot misread an interactive HTML file where you can just... click the thing and see what it does.

---

## What the Build Spec Became

Alongside the prototype, I wrote a full Python build specification: Dash for the UI layer, SQLite for the database, Google Calendar OAuth for sync, and standard pip/virtual environments for dependency management.

The spec goes into detail that surprised even me as I was writing it. The database schema has six tables. The history protocol specifies exactly what gets written on every mutation — a `moved` event includes both the source and destination day with human-readable labels, an `edited` event captures the field name plus before and after values, a `deleted` task gets copied to a tombstone table before the cascade. The event kinds, the service function signatures, the Pydantic models, the derived fields that should never be stored — all of it is in the spec.

The spec exists in this form because the prototype made it possible to write it. When the UI is settled, writing the data model that supports it is a much smaller exercise. The prototype answers "what data does this card need to show?" and the spec is just the formalisation of that answer.

Everything — the prototype React files, the HTML, and the full Python spec — is committed to the public GitHub repo. PR #1 is merged. The working directory is set.

---

## What Comes Next

Phase 1 of the Python build: repo scaffolding, the SQLite schema and migration runner, the core `create_task` and `list_tasks` service functions, and a Dash app that boots and shows a placeholder "Stride" page. That's it — no UI components, no board, no drag and drop. Just the foundation.

The discipline of stopping there matters. Phase 1 done correctly means Phase 2 (the board UI) has a stable backend to sit on. The build spec breaks the work into six phases for exactly this reason: each phase should produce something that runs, even if it doesn't do much yet.

I'll cover the Phase 1 and 2 build in the next post — what I actually sent to Claude Code, how it responded, where it got things right, and where I had to correct it.

In the meantime, if you want to look at what a Dash + SQLite task board spec looks like before a line of production code is written, the repo is public: https://github.com/FinancialRADDeveloper/stride

---

*Previous post: Choosing Your AI Assistants (And When to Switch)*
*Next post: Building the Board — Phase 1 and 2 with Claude Code*

---

**LinkedIn hook:** I built the full UI for my personal task board as a throwaway toy before writing any Python — and it changed how I work with AI coding assistants entirely. Here's why designing first makes AI-assisted implementation significantly more effective.
