// app.jsx — main Stride board

const { useState, useRef, useEffect, useMemo, useCallback } = React;

// ----- Seed -----------------------------------------------------------------
// Realistic personal/work mix inspired by the user's "distraction firewall" research.
// Dates anchored to TODAY (2026-05-12) so the demo stays consistent.

const seed = () => {
  const T = TODAY;
  const D = (off) => dayKey(addDays(T, off));
  const ts = (off, h = 9, m = 0) => {
    const d = addDays(T, off);
    d.setHours(h, m, 0, 0);
    return d.getTime();
  };
  const make = (overrides) => {
    const id = uid();
    const c = {
      id,
      title: '',
      description: '',
      priority: 'P3',
      size: 'M',
      category: 'personal',
      estimateMinutes: SIZES.M.minutes,
      timeOfDay: null,
      dayKey: D(0),
      done: false,
      createdAt: ts(-3, 9, 30),
      editCount: 0,
      moveCount: 0,
      calendarEvent: null,
      history: [],
      ...overrides,
    };
    if (c.history.length === 0) {
      c.history = [{ ts: c.createdAt, type: 'created' }];
    }
    return c;
  };

  return [
    // Today
    make({
      title: 'Draft Distraction Firewall — post 2 outline',
      description: 'Setting up an AI-First Development Workflow. Pull bullets from blog/blog-post-02.md, weave in lessons from CLAUDE.md setup, end on the "what a session looks like" section.',
      priority: 'P1', size: 'L', category: 'build', estimateMinutes: 120, timeOfDay: '09:30',
      dayKey: D(0),
      createdAt: ts(-1, 16, 12), calendarEvent: { eventId: 'gcal_b9x21f', calendarId: 'g_me_tasks', linkedAt: ts(0, 8, 5) },
      history: [
        { ts: ts(-1, 16, 12), type: 'created' },
        { ts: ts(-1, 16, 18), type: 'edited', field: 'description' },
        { ts: ts(0, 8, 5), type: 'scheduled', toValue: true },
      ],
      editCount: 1,
    }),
    make({
      title: 'Trial Superhuman Business — day 1 of 7',
      description: 'Enable Auto Labels for Marketing, News, Pitch, Social. Create splits: Important, VIP, Axiomix, Finance/Admin, Calendar, Waiting, Other.',
      priority: 'P2', size: 'M', category: 'build', estimateMinutes: 45, timeOfDay: '11:00',
      dayKey: D(0), createdAt: ts(-2, 10, 0),
      history: [
        { ts: ts(-2, 10, 0), type: 'created' },
        { ts: ts(-1, 9, 0), type: 'moved', from: 'Sun May 10', to: 'Mon May 11' },
        { ts: ts(0, 8, 30), type: 'moved', from: 'Mon May 11', to: 'Today' },
      ],
      moveCount: 2,
    }),
    make({
      title: '30m garage tidy',
      description: 'Recurring. Sweep bay, sort cardboard, water plants.',
      priority: 'P4', size: 'S', category: 'home', estimateMinutes: 30,
      dayKey: D(0), createdAt: ts(0, 7, 0),
      history: [{ ts: ts(0, 7, 0), type: 'created' }],
    }),
    make({
      title: 'Reply to Lewis re: meet-up',
      priority: 'P3', size: 'XS', category: 'personal', estimateMinutes: 10,
      dayKey: D(0), createdAt: ts(-4, 14, 0),
      history: [
        { ts: ts(-4, 14, 0), type: 'created' },
        { ts: ts(-3, 9, 0), type: 'moved', from: 'Fri May 8', to: 'Sat May 9' },
        { ts: ts(-2, 9, 0), type: 'moved', from: 'Sat May 9', to: 'Sun May 10' },
        { ts: ts(-1, 9, 0), type: 'moved', from: 'Sun May 10', to: 'Mon May 11' },
        { ts: ts(0, 9, 0), type: 'moved', from: 'Mon May 11', to: 'Today' },
      ],
      moveCount: 4,
    }),

    // Tomorrow
    make({
      title: 'Sketch SaneBox vs Zapier Personal Ops decision',
      description: 'Quick written comparison: setup effort, ongoing cost, level of control. Goal is a 1-pager I can refer back to in 3 months.',
      priority: 'P2', size: 'M', category: 'build', estimateMinutes: 75,
      dayKey: D(1), createdAt: ts(-2, 11, 0),
      history: [
        { ts: ts(-2, 11, 0), type: 'created' },
        { ts: ts(-1, 9, 0), type: 'edited', field: 'priority' },
      ],
      editCount: 1,
    }),
    make({
      title: 'Bike theory test prep — chapter 4',
      priority: 'P3', size: 'M', category: 'personal', estimateMinutes: 60, timeOfDay: '19:30',
      dayKey: D(1), createdAt: ts(-5, 19, 0),
      calendarEvent: { eventId: 'gcal_t73kx2', calendarId: 'g_me_tasks', linkedAt: ts(-1, 20, 0) },
      history: [
        { ts: ts(-5, 19, 0), type: 'created' },
        { ts: ts(-3, 9, 0), type: 'moved', from: 'Mon May 11', to: 'Tomorrow' },
        { ts: ts(-1, 20, 0), type: 'scheduled', toValue: true },
      ],
      moveCount: 1,
    }),
    make({
      title: 'BMW recall — book service slot',
      description: 'Email from Holdcroft references campaign 23V-061. Call number is in inbox.',
      priority: 'P1', size: 'S', category: 'admin', estimateMinutes: 20,
      dayKey: D(1), createdAt: ts(-1, 11, 0),
      history: [{ ts: ts(-1, 11, 0), type: 'created' }],
    }),
    make({
      title: 'Jira backlog grooming — Axiomix',
      priority: 'P2', size: 'L', category: 'work', estimateMinutes: 90, timeOfDay: '14:00',
      dayKey: D(1), createdAt: ts(0, 8, 0),
      history: [{ ts: ts(0, 8, 0), type: 'created' }],
    }),

    // +2
    make({
      title: 'Premium Bonds for kids — set up',
      description: 'Decision: £100 each per quarter. Need to fish out NS&I login from 1Password.',
      priority: 'P3', size: 'S', category: 'admin', estimateMinutes: 30,
      dayKey: D(2), createdAt: ts(-1, 21, 0),
      history: [{ ts: ts(-1, 21, 0), type: 'created' }],
    }),
    make({
      title: 'London Business School — CTO module 15 prep',
      description: 'Read pre-reading pack. Pages 4-22. Bring printed case study.',
      priority: 'P2', size: 'L', category: 'personal', estimateMinutes: 120, timeOfDay: '07:30',
      dayKey: D(2), createdAt: ts(-3, 9, 0),
      history: [{ ts: ts(-3, 9, 0), type: 'created' }, { ts: ts(-2, 10, 0), type: 'edited', field: 'description' }],
      editCount: 1,
    }),

    // +3
    make({
      title: 'Plan drink with Dan Wise',
      priority: 'P4', size: 'XS', category: 'personal', estimateMinutes: 10,
      dayKey: D(3), createdAt: ts(-2, 14, 0),
      history: [{ ts: ts(-2, 14, 0), type: 'created' }],
    }),
    make({
      title: 'eBay — list amazing prices',
      description: 'Three watches + the spare monitor. Photos already in iCloud.',
      priority: 'P3', size: 'L', category: 'admin', estimateMinutes: 150,
      dayKey: D(3), createdAt: ts(-6, 11, 0),
      history: [
        { ts: ts(-6, 11, 0), type: 'created' },
        { ts: ts(-4, 9, 0), type: 'moved', from: 'Thu May 7', to: 'Sat May 9' },
        { ts: ts(-2, 9, 0), type: 'moved', from: 'Sat May 9', to: 'Wed May 13' },
        { ts: ts(0, 8, 0), type: 'moved', from: 'Wed May 13', to: 'Fri May 15' },
      ],
      moveCount: 3,
    }),

    // +4
    make({
      title: 'Bedroom door — fix latch',
      priority: 'P4', size: 'S', category: 'home', estimateMinutes: 25,
      dayKey: D(4), createdAt: ts(-8, 19, 0),
      history: [
        { ts: ts(-8, 19, 0), type: 'created' },
        { ts: ts(-5, 9, 0), type: 'moved', from: 'Sun May 3', to: 'Wed May 6' },
        { ts: ts(-2, 9, 0), type: 'moved', from: 'Wed May 6', to: 'Sun May 10' },
        { ts: ts(0, 9, 0), type: 'moved', from: 'Sun May 10', to: 'Sat May 16' },
      ],
      moveCount: 3,
    }),
    make({
      title: 'Catalogue 5x watch chronographs',
      priority: 'P4', size: 'M', category: 'personal', estimateMinutes: 90,
      dayKey: D(4), createdAt: ts(-1, 22, 0),
      history: [{ ts: ts(-1, 22, 0), type: 'created' }],
    }),
    make({
      title: 'Organisation Hub — house revamp planning',
      description: 'Two evenings, big sheet of paper. Where things live, where they should live, what to bin.',
      priority: 'P3', size: 'XL', category: 'home', estimateMinutes: 240,
      dayKey: D(4), createdAt: ts(-3, 22, 0),
      history: [{ ts: ts(-3, 22, 0), type: 'created' }],
    }),

    // Already completed (Today)
    make({
      title: 'Morning kettlebell',
      priority: 'P3', size: 'S', category: 'health', estimateMinutes: 20,
      dayKey: D(0), done: true,
      createdAt: ts(0, 6, 0),
      history: [
        { ts: ts(0, 6, 0), type: 'created' },
        { ts: ts(0, 6, 45), type: 'done' },
      ],
    }),
  ];
};

// ----- App ------------------------------------------------------------------
const App = () => {
  const today = TODAY;
  const [t, setTweak] = useTweaks(window.TWEAK_DEFAULTS);
  const [cards, setCards] = useState(seed);
  const [weekOffset, setWeekOffset] = useState(0); // window start = today + weekOffset*7
  const [selectedId, setSelectedId] = useState(null);
  const [draggingId, setDraggingId] = useState(null);
  const [dropTarget, setDropTarget] = useState(null);
  const [composingFor, setComposingFor] = useState(null);
  const [showDone, setShowDone] = useState(true);
  const [filterCategory, setFilterCategory] = useState(null); // null = all

  const VIEW_DAYS = 6;
  const windowStart = useMemo(() => addDays(today, weekOffset * VIEW_DAYS), [today, weekOffset]);
  const days = useMemo(() => Array.from({ length: VIEW_DAYS }, (_, i) => addDays(windowStart, i)), [windowStart]);

  // Derive category list ordered by the default order, ignoring any deleted ones
  const categoryOrder = useMemo(() => {
    const fromTweaks = Object.keys(t.categories || {});
    const ordered = DEFAULT_CATEGORY_ORDER.filter(k => fromTweaks.includes(k));
    const extras = fromTweaks.filter(k => !DEFAULT_CATEGORY_ORDER.includes(k));
    return [...ordered, ...extras];
  }, [t.categories]);

  // Flatten calendars from all accounts for quick lookup
  const calendarsById = useMemo(() => {
    const map = {};
    for (const acc of (t.calendarAccounts || [])) {
      for (const cal of (acc.calendars || [])) {
        map[cal.id] = { ...cal, accountId: acc.id, provider: acc.provider, accountEmail: acc.email };
      }
    }
    return map;
  }, [t.calendarAccounts]);

  const selected = cards.find(c => c.id === selectedId) || null;

  // ----- Mutators ---------
  const tsNow = () => Date.now();

  const updateCard = useCallback((id, patch, fieldName) => {
    setCards(prev => prev.map(c => {
      if (c.id !== id) return c;
      const next = { ...c, ...patch };
      if (fieldName) {
        next.editCount = (c.editCount || 0) + 1;
        next.history = [...c.history, { ts: tsNow(), type: 'edited', field: fieldName }];
      }
      return next;
    }));
  }, []);

  const toggleDone = useCallback((id) => {
    setCards(prev => prev.map(c => {
      if (c.id !== id) return c;
      const done = !c.done;
      return {
        ...c,
        done,
        history: [...c.history, { ts: tsNow(), type: done ? 'done' : 'reopened' }],
      };
    }));
  }, []);

  const deleteCard = useCallback((id) => {
    setCards(prev => prev.filter(c => c.id !== id));
    setSelectedId(curr => curr === id ? null : curr);
  }, []);

  const moveCard = useCallback((id, toKey) => {
    setCards(prev => prev.map(c => {
      if (c.id !== id || c.dayKey === toKey) return c;
      const fromLabel = friendlyDay(parseKey(c.dayKey), today);
      const toLabel = friendlyDay(parseKey(toKey), today);
      return {
        ...c,
        dayKey: toKey,
        moveCount: (c.moveCount || 0) + 1,
        history: [...c.history, { ts: tsNow(), type: 'moved', from: fromLabel, to: toLabel }],
      };
    }));
  }, [today]);

  const setCardCalendar = useCallback((id, calendarId /* null to unlink */) => {
    setCards(prev => prev.map(c => {
      if (c.id !== id) return c;
      if (!calendarId) {
        if (!c.calendarEvent) return c;
        return {
          ...c,
          calendarEvent: null,
          history: [...c.history, { ts: tsNow(), type: 'scheduled', toValue: false, fromCalendarId: c.calendarEvent.calendarId }],
        };
      }
      // linking (or re-targeting to a different calendar)
      const eventId = c.calendarEvent?.eventId || ('gcal_' + Math.random().toString(36).slice(2, 8));
      const fromCalendarId = c.calendarEvent?.calendarId || null;
      return {
        ...c,
        calendarEvent: { eventId, calendarId, linkedAt: tsNow() },
        history: [...c.history, { ts: tsNow(), type: 'scheduled', toValue: true, calendarId, fromCalendarId }],
      };
    }));
  }, []);

  const addCard = useCallback((dayK, draft) => {
    const id = uid();
    const size = draft.size || 'M';
    const card = {
      id,
      title: draft.title.trim(),
      description: draft.description?.trim() || '',
      priority: draft.priority || 'P3',
      size,
      category: draft.category || 'personal',
      estimateMinutes: draft.estimateMinutes ?? SIZES[size].minutes,
      timeOfDay: draft.timeOfDay || null,
      dayKey: dayK,
      done: false,
      createdAt: tsNow(),
      editCount: 0,
      moveCount: 0,
      calendarEvent: null,
      history: [{ ts: tsNow(), type: 'created' }],
    };
    setCards(prev => [...prev, card]);
  }, []);

  // ----- Drag handlers ---------
  const onDragStart = (id) => setDraggingId(id);
  const onDragEnd = () => { setDraggingId(null); setDropTarget(null); };

  const onColumnDragOver = (e, k) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (dropTarget !== k) setDropTarget(k);
  };
  const onColumnDrop = (e, k) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('text/plain') || draggingId;
    if (id) moveCard(id, k);
    onDragEnd();
  };

  // ----- Keyboard ---------
  useEffect(() => {
    const h = (e) => {
      if (e.key === 'Escape') {
        setSelectedId(null);
        setComposingFor(null);
      }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  // ----- Grouping ---------
  const cardsByDay = useMemo(() => {
    const map = {};
    for (const d of days) map[dayKey(d)] = [];
    for (const c of cards) {
      if (!showDone && c.done) continue;
      if (filterCategory && c.category !== filterCategory) continue;
      if (map[c.dayKey]) map[c.dayKey].push(c);
    }
    // ordering: open first (by priority then created), then done
    for (const k of Object.keys(map)) {
      map[k].sort((a, b) => {
        if (a.done !== b.done) return a.done ? 1 : -1;
        const pa = PRIORITY_ORDER.indexOf(a.priority), pb = PRIORITY_ORDER.indexOf(b.priority);
        if (pa !== pb) return pa - pb;
        return a.createdAt - b.createdAt;
      });
    }
    return map;
  }, [cards, days, showDone, filterCategory]);

  // Cards not visible (off-window) summary
  const offWindowCount = useMemo(() => {
    const visKeys = new Set(days.map(d => dayKey(d)));
    return cards.filter(c => !visKeys.has(c.dayKey) && !c.done).length;
  }, [cards, days]);

  // counts per category, for legend chips (open tasks in window only)
  const categoryCounts = useMemo(() => {
    const visKeys = new Set(days.map(d => dayKey(d)));
    const out = {};
    for (const c of cards) {
      if (c.done) continue;
      if (!visKeys.has(c.dayKey)) continue;
      out[c.category] = (out[c.category] || 0) + 1;
    }
    return out;
  }, [cards, days]);

  return (
    <div style={{
      position: 'relative', height: '100%', display: 'flex', flexDirection: 'column',
      background: 'var(--bg)',
    }}>
      <TopBar
        today={today}
        windowStart={windowStart}
        onPrev={() => setWeekOffset(o => o - 1)}
        onNext={() => setWeekOffset(o => o + 1)}
        onToday={() => setWeekOffset(0)}
        offWindowCount={offWindowCount}
        showDone={showDone}
        onToggleDone={() => setShowDone(s => !s)}
      />

      {t.showLegend && (
        <Legend
          categories={t.categories}
          order={categoryOrder}
          active={filterCategory}
          onToggle={(cid) => setFilterCategory(prev => prev === cid ? null : cid)}
          counts={categoryCounts}
        />
      )}

      <Board
        days={days}
        today={today}
        cardsByDay={cardsByDay}
        categories={t.categories}
        calendarsById={calendarsById}
        showStaleRibbon={t.showStaleRibbon !== false}
        selectedId={selectedId}
        setSelectedId={setSelectedId}
        draggingId={draggingId}
        dropTarget={dropTarget}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
        onColumnDragOver={onColumnDragOver}
        onColumnDrop={onColumnDrop}
        composingFor={composingFor}
        setComposingFor={setComposingFor}
        onAdd={addCard}
        onToggleDone={toggleDone}
      />

      {selected && (
        <Detail
          card={selected}
          today={today}
          categories={t.categories}
          categoryOrder={categoryOrder}
          accounts={t.calendarAccounts || []}
          targets={{ personal: t.taskTargetPersonal, shared: t.taskTargetShared }}
          calendarsById={calendarsById}
          onClose={() => setSelectedId(null)}
          onChange={updateCard}
          onToggleDone={toggleDone}
          onDelete={deleteCard}
          onSetCardCalendar={setCardCalendar}
        />
      )}

      <StrideTweaks
        t={t}
        setTweak={setTweak}
        categoryOrder={categoryOrder}
      />
    </div>
  );
};

// counts shown next to legend chips (computed from current cards, ignoring done)
const Legend = ({ categories, order, active, onToggle, counts }) => {
  return (
    <div style={{
      flexShrink: 0,
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '8px 24px',
      borderBottom: '1px solid var(--line-soft)',
      background: 'var(--bg)',
      overflowX: 'auto',
    }}>
      <span className="mono" style={{
        fontSize: 10, letterSpacing: 0.6, textTransform: 'uppercase',
        color: 'var(--muted)', marginRight: 6,
      }}>Categories</span>
      {order.map(cid => {
        const cat = categories[cid];
        if (!cat) return null;
        const isActive = active === cid;
        const isDim = active && !isActive;
        const count = counts[cid] || 0;
        return (
          <button key={cid}
            onClick={() => onToggle(cid)}
            title={isActive ? 'Click to clear filter' : `Filter to ${cat.name}`}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              height: 24, padding: '0 9px', borderRadius: 999,
              fontSize: 11.5, fontWeight: 500,
              color: isDim ? 'var(--muted)' : 'var(--ink)',
              background: isActive ? cat.color : 'var(--surface-2)',
              border: `1px solid ${isActive ? cat.color : 'var(--line)'}`,
              opacity: isDim ? 0.55 : 1,
              transition: 'opacity 120ms ease',
            }}
          >
            <span style={{
              width: 8, height: 8, borderRadius: 2,
              background: isActive ? '#fff' : cat.color,
            }} />
            <span style={{ color: isActive ? '#fff' : 'inherit' }}>{cat.name}</span>
            <span className="mono" style={{
              fontSize: 10, opacity: 0.7,
              color: isActive ? '#fff' : 'var(--muted)',
            }}>{count}</span>
          </button>
        );
      })}
      {active && (
        <button onClick={() => onToggle(active)}
          className="mono"
          style={{
            marginLeft: 4, fontSize: 10.5, color: 'var(--muted)',
            display: 'inline-flex', alignItems: 'center', gap: 3,
          }}>
          <Icon name="x" size={9} /> clear filter
        </button>
      )}
    </div>
  );
};

// ----- Tweaks panel ---------------------------------------------------------
const StrideTweaks = ({ t, setTweak, categoryOrder }) => {
  const categories = t.categories || {};
  const accounts = t.calendarAccounts || [];
  const targets = { personal: t.taskTargetPersonal, shared: t.taskTargetShared };

  const updateCategory = (cid, patch) => {
    setTweak('categories', { ...categories, [cid]: { ...categories[cid], ...patch } });
  };
  const setVisibility = (calId, on) => {
    setTweak('calendarAccounts', accounts.map(acc => ({
      ...acc,
      calendars: acc.calendars.map(c => c.id === calId ? { ...c, visible: on } : c),
    })));
  };
  const setTarget = (slot /* 'personal' | 'shared' */, calId) => {
    const key = slot === 'personal' ? 'taskTargetPersonal' : 'taskTargetShared';
    setTweak(key, targets[slot] === calId ? null : calId);
  };

  return (
    <TweaksPanel title="Tweaks · Stride">
      <TweakSection label="Display" />
      <TweakToggle label="Show category legend"
        value={t.showLegend !== false}
        onChange={(v) => setTweak('showLegend', v)} />
      <TweakToggle label="Show STALE ribbon on cards moved 3+"
        value={t.showStaleRibbon !== false}
        onChange={(v) => setTweak('showStaleRibbon', v)} />

      <TweakSection label="Categories" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {categoryOrder.map(cid => (
          <CategoryRow key={cid} cid={cid} cat={categories[cid]} onUpdate={updateCategory} />
        ))}
      </div>

      <TweakSection label="Calendar accounts" />
      <div style={{
        fontSize: 10.5, color: 'rgba(41,38,27,.55)', lineHeight: 1.4,
        marginTop: -4, marginBottom: 4,
      }}>
        Toggles mirror Google Calendar — hidden calendars don't appear on the board.
        Two writable calendars can be marked as task targets.
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {accounts.map(acc => (
          <AccountBlock key={acc.id} acc={acc}
            targets={targets}
            onVisible={setVisibility}
            onTarget={setTarget} />
        ))}
      </div>
      <TweakButton secondary label="+ Connect another account" onClick={() => alert('Mocked: would open OAuth in the real build.')} />
    </TweaksPanel>
  );
};

const CategoryRow = ({ cid, cat, onUpdate }) => {
  if (!cat) return null;
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '4px 6px', borderRadius: 6,
      background: 'rgba(255,255,255,.5)',
      border: '0.5px solid rgba(0,0,0,.08)',
    }}>
      <ColorSwatchPicker value={cat.color} onChange={(v) => onUpdate(cid, { color: v })} />
      <input
        value={cat.name}
        onChange={(e) => onUpdate(cid, { name: e.target.value })}
        className="twk-field"
        style={{ height: 22, padding: '0 6px', flex: 1, minWidth: 0 }}
      />
      <span className="mono" style={{ fontSize: 9.5, color: 'rgba(41,38,27,.45)', minWidth: 38, textAlign: 'right' }}>
        {cid}
      </span>
    </div>
  );
};

const ColorSwatchPicker = ({ value, onChange }) => {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (!open) return;
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    window.addEventListener('mousedown', h);
    return () => window.removeEventListener('mousedown', h);
  }, [open]);
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button onClick={() => setOpen(o => !o)}
        title="Pick color"
        style={{
          width: 16, height: 16, borderRadius: 4, background: value,
          border: '1px solid rgba(0,0,0,.15)', cursor: 'pointer',
        }} />
      {open && (
        <div style={{
          position: 'absolute', top: 22, left: 0, zIndex: 30,
          background: 'rgba(255,255,255,.96)',
          border: '0.5px solid rgba(0,0,0,.15)',
          borderRadius: 8, padding: 6,
          boxShadow: '0 8px 24px rgba(0,0,0,.18)',
          display: 'grid', gridTemplateColumns: 'repeat(6, 16px)', gap: 4,
        }}>
          {CATEGORY_COLOR_PALETTE.map(c => (
            <button key={c}
              onClick={() => { onChange(c); setOpen(false); }}
              style={{
                width: 16, height: 16, borderRadius: 4, background: c,
                border: c === value ? '2px solid #16181d' : '1px solid rgba(0,0,0,.1)',
                cursor: 'pointer',
              }} />
          ))}
        </div>
      )}
    </div>
  );
};

const AccountBlock = ({ acc, targets, onVisible, onTarget }) => {
  return (
    <div style={{
      border: '0.5px solid rgba(0,0,0,.10)',
      borderRadius: 8, padding: 8,
      background: 'rgba(255,255,255,.5)',
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 6 }}>
        <span style={{
          fontSize: 9, letterSpacing: 0.6, textTransform: 'uppercase',
          padding: '1px 5px', borderRadius: 3,
          background: acc.provider === 'google' ? '#e8f0fe' : '#e6f3ee',
          color: acc.provider === 'google' ? '#1a73e8' : '#0a6f4a',
          fontWeight: 600,
        }} className="mono">{acc.provider}</span>
        <span style={{ fontSize: 11.5, fontWeight: 600 }}>{acc.label}</span>
      </div>
      <div className="mono" style={{ fontSize: 10, color: 'rgba(41,38,27,.5)', marginBottom: 6 }}>
        {acc.email}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {acc.calendars.map(cal => (
          <CalendarRow key={cal.id} cal={cal} targets={targets}
            onVisible={onVisible} onTarget={onTarget} />
        ))}
      </div>
    </div>
  );
};

const CalendarRow = ({ cal, targets, onVisible, onTarget }) => {
  const isPersonal = targets.personal === cal.id;
  const isShared = targets.shared === cal.id;
  const canWrite = cal.role !== 'reader';
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '3px 4px', borderRadius: 5,
      background: (isPersonal || isShared) ? 'rgba(0,0,0,.03)' : 'transparent',
    }}>
      {/* gcal-style checkbox: filled with calendar color when on */}
      <button onClick={() => onVisible(cal.id, !cal.visible)}
        title={cal.visible ? 'Hide on board' : 'Show on board'}
        style={{
          width: 14, height: 14, borderRadius: 3,
          background: cal.visible ? cal.color : 'transparent',
          border: `1.5px solid ${cal.color}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', flexShrink: 0,
        }}>
        {cal.visible && <Icon name="check" size={9} stroke={2.5} />}
      </button>
      <span style={{
        fontSize: 11.5, color: 'rgba(41,38,27,.85)',
        flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
      }}>{cal.name}</span>
      {cal.role === 'reader' && (
        <span className="mono" style={{ fontSize: 9, color: 'rgba(41,38,27,.4)' }}>read</span>
      )}
      {canWrite && (
        <>
          <button onClick={() => onTarget('personal', cal.id)}
            title="Use as personal task target (private)"
            style={{
              width: 18, height: 18, borderRadius: 4,
              background: isPersonal ? cal.color : 'transparent',
              color: isPersonal ? '#fff' : 'rgba(41,38,27,.4)',
              border: `0.5px solid ${isPersonal ? cal.color : 'rgba(0,0,0,.12)'}`,
              fontSize: 10, fontWeight: 600,
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            }}>P</button>
          <button onClick={() => onTarget('shared', cal.id)}
            title="Use as shared task target (visible to family)"
            style={{
              width: 18, height: 18, borderRadius: 4,
              background: isShared ? cal.color : 'transparent',
              color: isShared ? '#fff' : 'rgba(41,38,27,.4)',
              border: `0.5px solid ${isShared ? cal.color : 'rgba(0,0,0,.12)'}`,
              fontSize: 10, fontWeight: 600,
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            }}>S</button>
        </>
      )}
    </div>
  );
};

// ----- Top bar --------------------------------------------------------------
const TopBar = ({ today, windowStart, onPrev, onNext, onToday, offWindowCount, showDone, onToggleDone }) => {
  const monthLabel = `${MONTH_SHORT[windowStart.getMonth()]} ${windowStart.getFullYear()}`;
  return (
    <header style={{
      height: 56, flexShrink: 0,
      borderBottom: '1px solid var(--line)',
      background: 'var(--bg)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 24px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8, background: 'var(--ink)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--bg)', fontWeight: 700, fontSize: 14,
          }} className="mono">S</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, lineHeight: 1.1 }}>Stride</div>
            <div className="mono" style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: 0.3 }}>
              personal · day-board
            </div>
          </div>
        </div>
        <div style={{ width: 1, height: 24, background: 'var(--line)' }} />
        <div style={{ display: 'inline-flex', alignItems: 'baseline', gap: 12 }}>
          <h1 style={{ margin: 0, fontWeight: 600, fontSize: 18, letterSpacing: -0.2 }}>This week</h1>
          <span className="mono" style={{ fontSize: 12, color: 'var(--muted)' }}>{monthLabel}</span>
        </div>
      </div>

      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        {offWindowCount > 0 && (
          <span className="mono" style={{ marginRight: 12, fontSize: 11, color: 'var(--muted)' }}>
            <Icon name="inbox" size={11} stroke={1.5} style={{ marginRight: 4, verticalAlign: '-1px' }} />
            {offWindowCount} off-window
          </span>
        )}
        <button onClick={onToggleDone}
          title={showDone ? 'Hide completed' : 'Show completed'}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            height: 30, padding: '0 10px', borderRadius: 6,
            color: showDone ? 'var(--ink-2)' : 'var(--muted)',
            border: '1px solid var(--line)',
            background: 'var(--surface-2)',
            fontSize: 12, fontWeight: 500,
          }}>
          <Icon name="check" size={12} stroke={2} /> Completed
        </button>
        <div style={{ width: 8 }} />
        <button onClick={onPrev} title="Previous"
          style={btnIcon}><Icon name="chev_l" size={14} /></button>
        <button onClick={onToday}
          style={{ ...btnIcon, width: 'auto', padding: '0 12px', fontSize: 12, fontWeight: 500 }}>
          Today
        </button>
        <button onClick={onNext} title="Next"
          style={btnIcon}><Icon name="chev_r" size={14} /></button>
      </div>
    </header>
  );
};

const btnIcon = {
  width: 30, height: 30, borderRadius: 6,
  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
  border: '1px solid var(--line)', background: 'var(--surface-2)',
  color: 'var(--ink-2)',
};

// ----- Board ----------------------------------------------------------------
const Board = ({
  days, today, cardsByDay, categories, calendarsById, showStaleRibbon, selectedId, setSelectedId,
  draggingId, dropTarget, onDragStart, onDragEnd,
  onColumnDragOver, onColumnDrop,
  composingFor, setComposingFor, onAdd, onToggleDone,
}) => {
  return (
    <div style={{
      flex: 1, minHeight: 0, overflow: 'hidden',
      display: 'flex',
    }}>
      <div style={{
        flex: 1, minWidth: 0, overflowX: 'auto', overflowY: 'hidden',
        display: 'flex', gap: 0,
      }}>
        {days.map((d, i) => {
          const k = dayKey(d);
          const list = cardsByDay[k] || [];
          const isToday = daysBetween(today, d) === 0;
          const isPast = daysBetween(today, d) < 0;
          const isDrop = dropTarget === k;
          return (
            <Column
              key={k}
              day={d}
              cards={list}
              today={today}
              categories={categories}
              calendarsById={calendarsById}
              showStaleRibbon={showStaleRibbon}
              isToday={isToday}
              isPast={isPast}
              isDrop={isDrop}
              isFirst={i === 0}
              selectedId={selectedId}
              setSelectedId={setSelectedId}
              draggingId={draggingId}
              onDragStart={onDragStart}
              onDragEnd={onDragEnd}
              onColumnDragOver={(e) => onColumnDragOver(e, k)}
              onColumnDrop={(e) => onColumnDrop(e, k)}
              composing={composingFor === k}
              startCompose={() => setComposingFor(k)}
              cancelCompose={() => setComposingFor(null)}
              onAdd={(draft) => { onAdd(k, draft); setComposingFor(null); }}
              onToggleDone={onToggleDone}
            />
          );
        })}
      </div>
    </div>
  );
};

const friendlyDay = (d, today) => {
  const diff = daysBetween(today, d);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  if (diff === -1) return 'Yesterday';
  return `${WEEKDAY_SHORT[d.getDay()]} ${MONTH_SHORT[d.getMonth()]} ${d.getDate()}`;
};

// ----- Column ---------------------------------------------------------------
const Column = ({
  day, cards, today, categories, calendarsById, showStaleRibbon, isToday, isPast, isDrop, isFirst,
  selectedId, setSelectedId, draggingId, onDragStart, onDragEnd,
  onColumnDragOver, onColumnDrop,
  composing, startCompose, cancelCompose, onAdd, onToggleDone,
}) => {
  const k = dayKey(day);
  const openCards = cards.filter(c => !c.done);
  const totalMinutes = openCards.reduce((acc, c) => acc + (c.estimateMinutes || 0), 0);
  const CAPACITY = 480; // ~8h soft limit
  const capPct = Math.min(100, (totalMinutes / CAPACITY) * 100);
  const over = totalMinutes > CAPACITY;
  const label = dayLabel(day, today);

  return (
    <section
      onDragOver={onColumnDragOver}
      onDrop={onColumnDrop}
      style={{
        position: 'relative', flex: '0 0 312px', width: 312, height: '100%',
        display: 'flex', flexDirection: 'column',
        borderRight: '1px solid var(--line)',
        borderLeft: isFirst ? '1px solid var(--line)' : 'none',
        background: isDrop ? 'rgba(42, 74, 127, 0.05)' : 'transparent',
        transition: 'background 80ms ease',
      }}
    >
      {/* sticky-ish header */}
      <header style={{
        padding: '14px 16px 10px',
        borderBottom: '1px solid var(--line-soft)',
        background: isToday ? 'var(--surface)' : 'transparent',
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
          <div style={{ display: 'inline-flex', alignItems: 'baseline', gap: 8 }}>
            <h2 style={{
              margin: 0, fontSize: 15, fontWeight: 600, letterSpacing: -0.2,
              color: isPast ? 'var(--muted)' : 'var(--ink)',
            }}>{label}</h2>
            {isToday && (
              <span className="mono" style={{
                fontSize: 10, letterSpacing: 0.5, textTransform: 'uppercase',
                color: 'var(--coral)', fontWeight: 600,
              }}>now</span>
            )}
          </div>
          <span className="mono" style={{ fontSize: 11, color: 'var(--muted)' }}>
            {String(day.getDate()).padStart(2, '0')} {MONTH_SHORT[day.getMonth()]}
          </span>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, marginTop: 6,
        }}>
          <span className="mono" style={{ fontSize: 11, color: 'var(--muted)' }}>
            {openCards.length} open · {fmtMinutes(totalMinutes) || '0m'}
          </span>
          <div style={{ flex: 1 }} />
          <span className="mono" style={{
            fontSize: 10, color: over ? 'var(--coral)' : 'var(--muted)',
            fontWeight: over ? 600 : 400,
          }} title="Soft capacity: 8 hours">
            {Math.round((totalMinutes / CAPACITY) * 100)}%
          </span>
        </div>
        {/* capacity bar */}
        <div style={{
          marginTop: 4, height: 3, borderRadius: 2,
          background: 'var(--line-soft)', overflow: 'hidden',
        }}>
          <div style={{
            width: `${capPct}%`, height: '100%',
            background: over ? 'var(--coral)' : (capPct > 75 ? 'var(--amber)' : 'var(--olive)'),
            transition: 'width 200ms ease',
          }} />
        </div>
      </header>

      {/* card stack */}
      <div style={{
        flex: 1, minHeight: 0, overflowY: 'auto',
        padding: '8px 10px 4px',
        display: 'flex', flexDirection: 'column', gap: 6,
      }}>
        {cards.length === 0 && !composing && (
          <div style={{
            padding: '12px 14px', color: 'var(--muted)', fontSize: 12,
            border: '1px dashed var(--line)', borderRadius: 8,
            textAlign: 'center', marginTop: 4,
          }}>
            <span className="serif" style={{ fontSize: 13.5 }}>nothing for {label.toLowerCase()}</span>
          </div>
        )}
        {cards.map(c => (
          <Card
            key={c.id}
            card={c}
            today={today}
            categories={categories}
            calendarsById={calendarsById}
            showStaleRibbon={showStaleRibbon}
            isDragging={draggingId === c.id}
            isSelected={selectedId === c.id}
            onSelect={setSelectedId}
            onToggleDone={onToggleDone}
            onDragStart={onDragStart}
            onDragEnd={onDragEnd}
          />
        ))}

        {composing ? (
          <Composer onCancel={cancelCompose} onAdd={onAdd} categories={categories} />
        ) : (
          <button onClick={startCompose}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px 10px', marginTop: 2,
              color: 'var(--muted)', fontSize: 12,
              borderRadius: 8, border: '1px solid transparent',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--surface)'; e.currentTarget.style.color = 'var(--ink-2)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--muted)'; }}
          >
            <Icon name="plus" size={12} /> Add task
          </button>
        )}
        <div style={{ height: 16 }} />
      </div>
    </section>
  );
};

// ----- Composer (inline add) ------------------------------------------------
const Composer = ({ onAdd, onCancel, categories }) => {
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [priority, setPriority] = useState('P3');
  const [size, setSize] = useState('M');
  const [category, setCategory] = useState('personal');
  const [timeOfDay, setTimeOfDay] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const inputRef = useRef(null);
  useEffect(() => { inputRef.current?.focus(); }, []);

  const submit = () => {
    if (!title.trim()) return;
    onAdd({
      title, description: desc, priority, size, category,
      estimateMinutes: SIZES[size].minutes,
      timeOfDay: timeOfDay || null,
    });
  };

  const catList = DEFAULT_CATEGORY_ORDER.filter(c => categories[c]);
  const cat = categories[category] || { name: '—', color: 'var(--muted)' };

  return (
    <div style={{
      background: 'var(--surface-2)', border: '1px solid var(--ink)',
      borderRadius: 'var(--radius-card)', padding: 10,
      boxShadow: 'var(--shadow-card-hover)',
      position: 'relative',
    }}>
      <div title={cat.name} style={{
        position: 'absolute', left: 0, top: 8, bottom: 8, width: 3,
        background: cat.color, borderRadius: '0 2px 2px 0',
      }} />
      <input
        ref={inputRef}
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Task title"
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); } if (e.key === 'Escape') onCancel(); }}
        style={{
          width: '100%', border: 0, background: 'transparent',
          fontSize: 14, fontWeight: 500, color: 'var(--ink)',
          padding: '2px 0 2px 4px',
        }}
      />
      {showAdvanced && (
        <textarea
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
          placeholder="Description (optional)"
          rows={2}
          style={{
            width: '100%', resize: 'none', border: 0, background: 'transparent',
            fontSize: 12, color: 'var(--ink-2)', padding: '4px 4px', marginTop: 4,
          }}
        />
      )}
      {/* category row */}
      <div style={{ display: 'flex', gap: 4, marginTop: 6, flexWrap: 'wrap', paddingLeft: 4 }}>
        {catList.map(cid => {
          const c = categories[cid];
          const sel = cid === category;
          return (
            <button key={cid} onClick={() => setCategory(cid)}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                padding: '0 6px', height: 20, borderRadius: 4,
                fontSize: 10.5, fontWeight: 500,
                color: sel ? '#fff' : 'var(--ink-2)',
                background: sel ? c.color : 'transparent',
                border: `1px solid ${sel ? c.color : 'var(--line)'}`,
              }}>
              <span style={{ width: 6, height: 6, borderRadius: 1.5, background: sel ? '#fff' : c.color }} />
              {c.name}
            </button>
          );
        })}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6, paddingLeft: 4 }}>
        {/* priority */}
        <div style={{ display: 'inline-flex', gap: 2 }}>
          {PRIORITY_ORDER.map(p => {
            const sel = p === priority;
            const cfg = PRIORITIES[p];
            return (
              <button key={p} onClick={() => setPriority(p)} className="mono"
                style={{
                  padding: '0 6px', height: 22, borderRadius: 4, fontSize: 10.5, fontWeight: 600,
                  color: sel ? '#fff' : cfg.color, background: sel ? cfg.color : cfg.bg,
                  border: 0,
                }}>{p}</button>
            );
          })}
        </div>
        <div style={{ width: 4 }} />
        {/* size */}
        <div style={{ display: 'inline-flex', gap: 2 }}>
          {SIZE_ORDER.map(s => {
            const sel = s === size;
            return (
              <button key={s} onClick={() => setSize(s)} className="mono"
                style={{
                  padding: '0 6px', height: 22, borderRadius: 4, fontSize: 10.5, fontWeight: 600,
                  color: sel ? '#fff' : 'var(--ink-2)', background: sel ? 'var(--ink)' : 'transparent',
                  border: '1px solid ' + (sel ? 'var(--ink)' : 'var(--line)'),
                }}>{s}</button>
            );
          })}
        </div>
        <div style={{ flex: 1 }} />
        <input type="time" value={timeOfDay} onChange={(e) => setTimeOfDay(e.target.value)}
          style={{
            padding: '0 6px', height: 22, fontSize: 11,
            border: '1px solid var(--line)', borderRadius: 4,
            background: 'transparent', fontFamily: 'Geist Mono, monospace',
          }} />
        <button onClick={() => setShowAdvanced(s => !s)} title="Toggle description"
          className="mono"
          style={{
            height: 22, padding: '0 6px', fontSize: 10.5, color: 'var(--muted)',
            border: '1px solid var(--line)', borderRadius: 4,
          }}>{showAdvanced ? '–' : '+'} desc</button>
      </div>
      <div style={{ display: 'flex', gap: 6, marginTop: 8, justifyContent: 'flex-end' }}>
        <button onClick={onCancel}
          style={{ padding: '4px 10px', fontSize: 12, color: 'var(--muted)', borderRadius: 4 }}>
          Cancel
        </button>
        <button onClick={submit}
          disabled={!title.trim()}
          style={{
            padding: '4px 12px', fontSize: 12, fontWeight: 500,
            background: title.trim() ? 'var(--ink)' : 'var(--line)',
            color: title.trim() ? 'var(--bg)' : 'var(--muted)',
            borderRadius: 4,
          }}>
          Add task
        </button>
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
