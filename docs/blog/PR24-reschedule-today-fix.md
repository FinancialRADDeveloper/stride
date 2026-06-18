# The One-Line Bug: Why "Today" Needed Its Own Conditional

PR #24 is a bug fix. The bug was one line. The fix was one line. The lesson inside it — about boundary conditions in time-based UI logic — is worth the time to explain properly.

---

## The Bug

The reschedule modal from PR #23 showed a "Reschedule →" button on past-date columns. The condition:

```python
if is_past and open_tasks:
    show_reschedule_button()
```

The bug: this condition showed the button on past columns only. Today's column is not a past column. By this condition, today never got a Reschedule button.

But today's column frequently has overdue tasks — tasks that were added in the morning and not completed, tasks rolled over from yesterday, tasks that simply did not get done. "Today" is, for planning purposes, often the most important column to have a Reschedule button on.

The fix:

```python
if (is_past or is_today) and open_tasks:
    show_reschedule_button()
```

One character added, one bug fixed.

---

## Why This Bug Exists

The `is_past`, `is_today`, and `is_future` flags in the board rendering logic are derived from comparing each column's `day_key` to today's date:

```python
today_str = date.today().isoformat()
is_today = day_key == today_str
is_past = day_key < today_str
is_future = day_key > today_str
```

These three flags are mutually exclusive and exhaustive — every column is exactly one of past, today, or future. But they do not map cleanly to UI concerns.

The initial intuition was: "Reschedule is for past tasks." Past tasks are the ones that accumulate on columns from previous days. Today's tasks are... today's tasks. They should get done today.

The reality: on a busy day or after a few days of not opening Stride, today's column can have ten open tasks that were pushed there from yesterday's Reschedule action. They are all overdue. The Reschedule button is useful there.

The sharp boundary between `is_past` and `is_today` required explicit handling. "Past" and "today" are distinct for date comparison purposes. For the Reschedule button's purpose, they are the same thing: "this column has tasks that may not get done today."

---

## The Pattern: Today Is a Third State

Today's column occupies a third state in many conditional branches in Stride's board logic:

- **Past:** tasks are overdue; column header shows in muted colour; Reschedule button shown
- **Today:** tasks are due; column header is prominent; Reschedule button needed (after this fix)
- **Future:** tasks are planned; column is displayed normally; no Reschedule button

The correct mental model is that "past" and "today" share a "needs attention" property while "future" is "planned." The boolean flag approach (`is_past`, `is_today`, `is_future`) makes this property implicit — you have to combine `is_past or is_today` everywhere the "needs attention" concept applies.

An alternative design would define an explicit `is_current_or_past` property. This is worth doing if the conditional recurs in many places. In Stride's current implementation, it recurs in one place, so the inline `or` is cleaner than introducing a new property.

---

## The Broader Lesson: Test Time Boundaries

Time-based UI logic has inherent edge cases at the boundaries: midnight transitions, the exact current day, the transition between "this week" and "last week." These boundaries are easy to test at development time (simply run the tests with a forced date), but they are invisible during development if you always open the board mid-morning on a weekday.

The "today" column is the most important boundary in Stride's board logic. It is the column that changes meaning day to day — yesterday's today is today's past. Every conditional that distinguishes past, today, and future needs explicit verification that "today" is handled correctly, not implicitly assumed to behave like one of the other two.

After PR #24, a comment was added to the column rendering logic:

```python
# Note: today requires explicit handling in conditions that treat past and today
# the same way (e.g., Reschedule button). is_today is NOT included in is_past.
```

This comment prevents the bug from being re-introduced in future PRs that add new conditional UI to column rendering.

---

## What the AI-Assisted Workflow Actually Looked Like

The bug was found during daily use — clicking the board on a day with overdue tasks in today's column and wondering why there was no Reschedule button.

The diagnosis was immediate: the condition only checked `is_past`. The fix was `is_past or is_today`. The AI confirmed this was correct and suggested the defensive comment.

Total time from observation to merged fix: fifteen minutes, including the PR description. This is the correct amount of time for a one-line bug fix — investigate, understand, fix, document, ship.

---

## What This Unlocks

A Reschedule button on today's column when there are open tasks. The daily workflow improvement is small but real: on mornings where the previous day's tasks rolled over or accumulated, they can be bulk-rescheduled from today's column to a future date (or kept on today if that is the intent).

---

## Takeaway for Consultants

One-line fixes deserve proper diagnosis and documentation. The fix is trivial. The understanding — why today is a third state in time-based UI logic, why `is_past` and `is_today` are distinct, why the Reschedule button belongs on both — is what prevents the bug from returning. Write a comment that explains the distinction. Future you will thank present you.

Time boundaries in UI logic are where the most subtle bugs live. Test every day of the week, not just weekdays. Test "today" explicitly, not as an assumed default.

---

## LinkedIn Summary

A one-line bug in Stride's column rendering excluded today from the Reschedule button logic. The fix was `is_past or is_today`. The lesson: in time-based UI, "today" is a third state — not past, not future — and every conditional that conflates it with either will produce a bug. A comment explaining the distinction costs nothing and prevents the bug from returning. Short PRs deserve proper diagnosis.
