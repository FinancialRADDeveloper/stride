# Claude Best Practices for Professional Development

A comprehensive guide to using Claude effectively as an AI coding assistant, optimizing costs, and building in public.

## Table of Contents

1. [Claude Code CLI Best Practices](#claude-code-cli-best-practices)
2. [Token Cost Optimization](#token-cost-optimization)
3. [Prompt Engineering for Coding](#prompt-engineering-for-coding)
4. [Multi-Agent Patterns](#multi-agent-patterns)
5. [Project Setup & Configuration](#project-setup--configuration)
6. [Working with Multiple AI Tools](#working-with-multiple-ai-tools)
7. [Security & Safety](#security--safety)
8. [Quick Reference](#quick-reference)

---

## Claude Code CLI Best Practices

### Understanding CLAUDE.md

The `CLAUDE.md` file is the central knowledge artifact for your project. It serves as persistent memory that Claude Code reads at the start of every session.

**Structure and Content:**

```markdown
# Project Name

## Overview
[Brief 2-3 sentence description of the project]

## Architecture
[Key architectural decisions, patterns, structure]

## Current State
[What's complete, what's in progress]

## Key Files & Their Purpose
- `src/main.ts` — Entry point, initializes the application
- `src/components/` — React components, organized by feature
- `docs/` — Generated API documentation

## Development Guidelines
[Testing strategy, code style, deployment process]

## Known Limitations & TODOs
[Technical debt, blocked items, future improvements]

## Recent Context
[Recent changes, active branches, current focus]
```

**Best Practices:**

- **Keep it updated** — After major sessions, add what you learned to CLAUDE.md. Use the `claude-md-management` skill to capture learnings.
- **Be specific** — Generic descriptions like "handles authentication" are less useful than "uses JWT tokens with 1-hour expiry, stored in httpOnly cookies, refreshed via `/refresh` endpoint"
- **Include non-obvious patterns** — Document why you chose certain patterns, not just what they are
- **List key dependencies** — Critical packages, their versions, and any version constraints
- **Record decisions** — Why certain tech choices were made helps avoid repeating old discussions
- **Keep examples** — Include code snippets for common patterns in your project

### Memory System

Claude Code maintains multiple memory layers:

**Session Memory:**
- Within a session, Claude retains context across multiple turns
- Ideal for tasks that span multiple interactions without re-reading files

**CLAUDE.md Memory:**
- Persistent across sessions
- Should contain high-level architecture, key decisions, current state
- Read automatically at session start

**Memory Files (.claude/):**
- Optional persistent storage for detailed context
- Use for: learnings, patterns discovered, architectural insights

**When to Use Each:**

```
Session Memory     → Single-session debugging, active task work
CLAUDE.md          → Architecture, design decisions, code structure
Memory Files       → Cross-session learnings, discovered patterns, team notes
```

### Hooks & Automated Workflows

Hooks in `settings.json` enable Claude to automate common tasks.

**Common Hook Patterns:**

```json
{
  "hooks": {
    "beforeCommit": {
      "command": "npm run lint && npm run test"
    },
    "afterBranch": {
      "command": "npm install"
    }
  }
}
```

**Best Practices:**

- **Keep hooks lightweight** — Long-running hooks slow down workflows
- **Fail gracefully** — Hooks that fail should provide clear error messages
- **Use for validation, not generation** — Hooks should validate code, not generate it
- **Document expectations** — If a hook requires certain tools installed, document this in CLAUDE.md

### Slash Commands & CLI Tools

Slash commands provide quick access to common operations:

```
/help              → See available commands
/config            → Quick access to settings
/loop              → Run a task on recurring interval
/schedule          → Create scheduled agents
/review            → Trigger code review
/security-review   → Security audit of pending changes
```

### Permissions & Secure Operation

Claude Code uses permission tiers to control what operations are allowed:

**Permission Levels:**

1. **Read-only** — Browsing, searching, reading files
2. **Execute** — Running tests, linting, builds
3. **Write** — File modifications, git operations
4. **Full** — Unrestricted access

**Setting Permissions in settings.json:**

```json
{
  "permissions": {
    "global": ["read", "execute"],
    "projects": {
      "my-project": ["read", "execute", "write"]
    }
  }
}
```

### MCP Servers for Extended Capabilities

Claude Code connects to Model Context Protocol (MCP) servers for specialized tools (Todoist, Gmail, GitHub, Jira, Slack, Linear, etc.).

**Best Practices:**
- Enable only what you need — each MCP adds startup latency
- Use environment variables for credentials — never store secrets in config files
- Document MCP usage — explain how your project uses each MCP

---

## Token Cost Optimization

### Understanding Claude's Token Economy

Claude's pricing is based on input tokens (what you send) and output tokens (what it generates).

**Current Pricing Reference (as of May 2026):**
- **Claude Sonnet**: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- **Claude Opus**: ~$15 per 1M input tokens, ~$75 per 1M output tokens
- **Claude Haiku**: ~$0.80 per 1M input tokens, ~$4 per 1M output tokens

### Prompt Caching

Prompt caching is the single biggest token optimization available. Cached sections are charged at **10% of normal input cost** after the first request.

**How it Works:**

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    system=[
        {
            "type": "text",
            "text": large_context,  # Your codebase, docs, etc.
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[{"role": "user", "content": "Your question"}]
)
```

**Cache Mechanics:**

- **Cache TTL**: 5 minutes (resets on each cache hit)
- **Minimum cache size**: 1,024 tokens
- **Cost savings**: 90% discount on cached tokens after first request

**What to Cache:**

```
CACHE THESE:              DON'T CACHE:
System prompts            User questions (low reuse)
Codebase structure        One-time data
API documentation         Volatile information
Testing frameworks        Real-time context
Shared knowledge bases    Short snippets
```

### Avoiding Unnecessary Context

**Context Bloat Costs Money:**

Instead of pasting entire files, provide:
1. The specific function or snippet relevant to the question
2. The exact error message
3. What you've already tried
4. What you expect vs. what's happening

**Progressive Disclosure:**
1. Ask the question without context
2. If Claude needs more, provide specific files/snippets
3. Avoid pre-emptively dumping everything

### Batch API for 50% Savings

For non-interactive use cases (scheduled tasks, reports, bulk review):

```python
batch = client.beta.messages.batches.create(
    requests=[
        {
            "custom_id": "request-1",
            "params": {
                "model": "claude-sonnet-4-6",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Request 1"}]
            }
        }
    ]
)
```

### Model Selection: Opus vs Sonnet vs Haiku

| Task | Recommended Model | Why |
|------|------------------|-----|
| New feature implementation | Sonnet | Good coding + reasoning |
| Architecture design review | Opus | Need strongest reasoning |
| Complex refactoring | Opus | Understanding legacy code |
| Code linting/classification | Haiku | Simple, fast, cheap |
| Documentation generation | Sonnet | Quality matters, reasonable cost |
| Automated testing | Haiku | Fast, high volume |
| Debugging production issue | Sonnet | Balance of speed + depth |
| PR review (non-critical) | Sonnet | Good balance |

**Rule of thumb:** Default to Sonnet. Use Opus when Sonnet gives mediocre results on complex reasoning. Use Haiku for high-volume simple tasks.

### Token Budget Estimation

```
Small bug fix:        3,000–5,000 tokens    (~$0.015–0.025)
Medium feature:      10,000–20,000 tokens   (~$0.05–0.10)
Large refactoring:   30,000–50,000 tokens   (~$0.15–0.30)
Architecture design: 20,000–40,000 tokens   (~$0.10–0.20)

Cost-saving tactics:
- Prompt caching:  -90% on cached input tokens
- Batch API:       -50% on total cost
- Haiku for simple tasks: -75% vs Sonnet
```

---

## Prompt Engineering for Coding

### The Core Template

```
[CONTEXT]
I'm working on [what you're building]
Stack: [languages, frameworks, key libraries]
Current state: [what works, what doesn't]

[PROBLEM]
I'm trying to [what you want to achieve]
Error/issue: [specific error message or description]

[EVIDENCE]
Here's the relevant code:
[minimal code snippet — not entire file]

[SPECIFIC QUESTION]
Why does [X happen]?
```

### When to Use Extended Thinking

Extended thinking is Claude's ability to reason through complex problems before responding. It uses more tokens but produces higher quality on genuinely difficult tasks.

**Use it for:**
- Complex architectural decisions
- Algorithm design with multiple constraints
- Intermittent/race condition bugs
- Security review of critical code

**Skip it for:**
- Simple refactoring, syntax errors, one-liners

### Code Review Prompts

```
I have a Pull Request that [brief description].
Here's the code:
[paste the changed lines, not entire files]

Review for:
1. Correctness — will this work as intended?
2. Performance — any obvious inefficiencies?
3. Security — any vulnerabilities?
4. Style — does it match the codebase style?

Context: [any specific concerns]
```

### Debugging Prompts

```
I'm debugging a [error type] that happens when [condition].

Error message: [full error stack trace]

Here's the relevant code:
[minimal reproducible code]

What I've tried: [thing 1], [thing 2]

Expected: [what should happen]
Actual: [what actually happens]
```

---

## Multi-Agent Patterns

### When to Spawn Subagents

**Good candidates:**
- Parallel code review of multiple independent modules
- Running tests while documentation is being written
- Long-running build processes in the background
- Independent research tasks

**Poor candidates:**
- Highly interdependent changes
- Tasks requiring immediate feedback loops
- Work requiring shared mutable state

### Worktree Isolation

Subagents work in isolated git worktrees — no branch conflicts, easy cherry-picking, clean git history.

### Parallel vs Sequential Agents

```
PARALLEL: Tasks with no dependencies on each other
  - API refactoring
  - Documentation updates

SEQUENTIAL: Tasks that depend on prior results
  - Schema refactoring → Data migration → ORM updates
```

### Communication Between Agents

Agents communicate via:
1. **Git commits** — Each agent commits work to separate branches
2. **CLAUDE.md updates** — Shared knowledge base
3. **Shared test results** — Via git (test reports committed)

---

## Project Setup & Configuration

### CLAUDE.md Structure

See [project-settings.md](../project-settings.md) for the project-level configuration. A good CLAUDE.md should include:

- Quick summary (1-2 sentences)
- Tech stack with specific versions
- Architecture overview
- Key components & their responsibilities
- Development workflow (commands to run, branch strategy)
- Current state (what's done, what's in progress)
- Known limitations & TODOs
- Code style & conventions
- External dependencies & services
- Recent learnings

### settings.json Configuration

```json
{
  "model": "claude-sonnet-4-6",
  "maxTokens": 4096,
  "permissions": {
    "global": ["read", "execute"],
    "projects": {
      "this-project": ["read", "execute", "write"]
    }
  },
  "hooks": {
    "beforeCommit": {
      "command": "npm run lint && npm run test --passWithNoTests",
      "timeout": 30000
    }
  }
}
```

### .claude/ Directory Structure

```
.claude/
├── CLAUDE.md                    # Core project documentation
├── settings.json                # Project-specific config
├── settings.local.json          # Local overrides (git-ignored)
└── memory/
    ├── learnings.md             # Patterns discovered
    └── architecture.md          # Deep architecture notes
```

---

## Working with Multiple AI Tools

### Claude + Cursor

| Task | Best Tool | Why |
|------|-----------|-----|
| Writing new code | Cursor | Real-time editing, autocomplete |
| Refactoring | Cursor | See changes in-editor immediately |
| Architecture design | Claude Code | No IDE bias, clearer reasoning |
| Batch code review | Claude Code | Better for multiple files |
| Complex bug investigation | Claude Code | Better conversation memory |
| Test writing | Cursor | Quick iteration with IDE feedback |

### Claude + Codex / Copilot

- **Copilot**: Fast inline completions, trained on open source — great for boilerplate
- **Claude**: Better reasoning, understands your specific project context — great for review and debugging

**Pattern:** Copilot generates the shell, Claude reviews it, Copilot completes the helpers, Claude debugs complex logic.

### Claude + Junie (JetBrains AI)

- **Junie**: Quick inline refactors, method extraction in the IDE
- **Claude**: Full-module refactoring, architectural changes

### Multi-Tool Best Practices

1. **One tool leads per task** — Don't split architecture across three tools
2. **Consolidate learnings** — After a multi-tool session, update CLAUDE.md with what you discovered
3. **Clear context switching** — Commit work-in-progress before switching tools; update CLAUDE.md with current state

---

## Security & Safety

### Avoiding Credential Leaks

**Golden Rule: Never paste secrets into conversations.**

```javascript
// ❌ LEAKED
const apiKey = "sk-abc123def456";

// ✅ SAFE
const apiKey = process.env.API_KEY;
```

When showing code to Claude, redact actual key values and note they come from environment variables.

### Safe Environment Setup

```bash
.env                    # Local development (git-ignored)
.env.example           # Template without secrets (committed)
.env.production        # Only on production servers
```

### Security Code Review Checklist

Ask Claude to check:
1. Input validation (XSS, injection attacks)
2. Authentication (are checks present?)
3. Authorization (can this user do this action?)
4. Hardcoded credentials
5. SQL injection (parameterized queries?)
6. CORS misconfiguration
7. Rate limiting on API endpoints
8. Sensitive data in logs

### Reviewing Commands Claude Proposes

Before running any command Claude suggests:
1. Understand what it does
2. Check if it has side effects (DB changes, network calls, file deletions)
3. Verify the environment is correct (dev vs. prod)
4. Confirm you can roll back if needed

---

## Quick Reference

### Essential Claude Code Commands

```
/help              → Available commands
/config            → Settings
/review            → Code review
/security-review   → Security audit
/loop 5m /task     → Repeat task every 5 minutes
```

### Performance Metrics to Track

```
Frontend:
- LCP (Largest Contentful Paint):  target <2.5s
- FID (First Input Delay):         target <100ms
- Bundle size:                     target <200KB gzipped

Backend:
- API response time (p95):         target <200ms
- Database query time (p95):       target <50ms
- Cache hit rate:                  target >80%
- Error rate:                      target <0.1%
```

### The Compounding Advantage

The highest-leverage habit: **update CLAUDE.md at the end of every meaningful session.**

Each update compounds — future sessions start smarter, context switches are cheaper, and onboarding new tools (or new team members) is faster. This is the single practice that separates developers who get 2x value from AI tools from those who get 10x.

---

**Document version:** 1.0  
**Last updated:** 2026-05-11  
**Source:** Research sub-agent synthesis
