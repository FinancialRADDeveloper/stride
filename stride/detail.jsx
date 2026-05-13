// detail.jsx — right-side card detail panel

const PriorityPicker = ({ value, onChange }) => (
  <div style={{ display: 'inline-flex', gap: 4 }}>
    {PRIORITY_ORDER.map(p => {
      const sel = p === value;
      const cfg = PRIORITIES[p];
      return (
        <button key={p}
          onClick={() => onChange(p)}
          className="mono"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '4px 10px', height: 28, borderRadius: 6, fontSize: 12, fontWeight: 500,
            color: sel ? '#fff' : cfg.color,
            background: sel ? cfg.color : cfg.bg,
            border: `1px solid ${sel ? cfg.color : 'transparent'}`,
          }}>
          <span style={{ width: 6, height: 6, borderRadius: 999, background: sel ? '#fff' : cfg.color }} />
          {p}
        </button>
      );
    })}
  </div>
);

const SizePicker = ({ value, onChange }) => (
  <div style={{ display: 'inline-flex', gap: 4 }}>
    {SIZE_ORDER.map(s => {
      const sel = s === value;
      return (
        <button key={s}
          onClick={() => onChange(s)}
          className="mono"
          title={SIZES[s].hint}
          style={{
            padding: '4px 10px', height: 28, borderRadius: 6, fontSize: 12, fontWeight: 500,
            color: sel ? '#fff' : 'var(--ink-2)',
            background: sel ? 'var(--ink)' : 'transparent',
            border: `1px solid ${sel ? 'var(--ink)' : 'var(--line)'}`,
          }}>
          {s}
        </button>
      );
    })}
  </div>
);

const CategoryPicker = ({ value, onChange, categories, order }) => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
    {order.map(cid => {
      const cat = categories[cid];
      if (!cat) return null;
      const sel = cid === value;
      return (
        <button key={cid}
          onClick={() => onChange(cid)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '4px 10px', height: 28, borderRadius: 6, fontSize: 12, fontWeight: 500,
            color: sel ? '#fff' : 'var(--ink-2)',
            background: sel ? cat.color : 'transparent',
            border: `1px solid ${sel ? cat.color : 'var(--line)'}`,
          }}>
          <span style={{
            width: 8, height: 8, borderRadius: 2,
            background: sel ? '#fff' : cat.color,
          }} />
          {cat.name}
        </button>
      );
    })}
  </div>
);

const CalendarChooser = ({ card, accounts, targets, onSetCardCalendar }) => {
  // Flatten writable calendars across accounts for the "pick a specific one" menu.
  const writable = [];
  for (const acc of accounts) {
    for (const cal of (acc.calendars || [])) {
      if (cal.role !== 'reader') writable.push({ ...cal, accountId: acc.id, provider: acc.provider, accountEmail: acc.email });
    }
  }
  const byId = Object.fromEntries(writable.map(c => [c.id, c]));
  const linkedId = card.calendarEvent?.calendarId || null;
  const linked = linkedId ? byId[linkedId] : null;

  const personal = targets.personal ? byId[targets.personal] : null;
  const shared   = targets.shared   ? byId[targets.shared]   : null;

  const isOnPersonal = personal && linkedId === personal.id;
  const isOnShared   = shared   && linkedId === shared.id;
  const isOnOther    = !!linkedId && !isOnPersonal && !isOnShared;

  const [menuOpen, setMenuOpen] = React.useState(false);
  const menuRef = React.useRef(null);
  React.useEffect(() => {
    if (!menuOpen) return;
    const h = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false); };
    window.addEventListener('mousedown', h);
    return () => window.removeEventListener('mousedown', h);
  }, [menuOpen]);

  const tri = (active, color, label, hint, onClick, disabled) => (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={disabled ? 'No calendar set for this target — pick one in Tweaks' : ''}
      style={{
        flex: 1, textAlign: 'left',
        display: 'flex', alignItems: 'flex-start', gap: 8,
        padding: '10px 12px', borderRadius: 8,
        border: `1px solid ${active ? (color || 'var(--ink)') : 'var(--line)'}`,
        background: active ? (color ? `${color}14` : 'var(--surface-2)') : 'var(--surface-2)',
        color: 'var(--ink)', cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
      }}>
      <span style={{
        width: 12, height: 12, borderRadius: 3, marginTop: 1, flexShrink: 0,
        background: color || 'var(--muted)',
        border: active ? `2px solid #fff` : '1px solid rgba(0,0,0,.15)',
        boxShadow: active ? `0 0 0 1.5px ${color || 'var(--ink)'}` : 'none',
      }} />
      <span style={{ minWidth: 0, flex: 1 }}>
        <div style={{ fontSize: 12.5, fontWeight: 600, lineHeight: 1.2 }}>{label}</div>
        <div className="mono" style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 2, lineHeight: 1.2 }}>
          {hint}
        </div>
      </span>
    </button>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', gap: 6 }}>
        {tri(
          !linkedId, null, 'Don\u2019t schedule', 'task stays on the board only',
          () => onSetCardCalendar(card.id, null),
          false,
        )}
        {tri(
          isOnPersonal, personal?.color, 'Personal',
          personal ? personal.name : 'no target set',
          () => onSetCardCalendar(card.id, personal.id),
          !personal,
        )}
        {tri(
          isOnShared, shared?.color, 'Shared',
          shared ? shared.name : 'no target set',
          () => onSetCardCalendar(card.id, shared.id),
          !shared,
        )}
      </div>

      {/* pick a specific one */}
      <div ref={menuRef} style={{ position: 'relative' }}>
        <button onClick={() => setMenuOpen(o => !o)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            height: 28, padding: '0 10px', borderRadius: 6, fontSize: 11.5,
            border: '1px solid var(--line)', background: 'var(--surface-2)',
            color: 'var(--ink-2)', fontWeight: 500,
          }}>
          {linked ? (
            <>
              <span style={{ width: 8, height: 8, borderRadius: 2, background: linked.color }} />
              <span>{linked.name}</span>
              <span className="mono" style={{ color: 'var(--muted)', fontSize: 10 }}>
                · {linked.provider}
              </span>
            </>
          ) : (
            <>
              <Icon name="cal" size={11} />
              <span>Pick a specific calendar</span>
            </>
          )}
          <Icon name="chev_d" size={10} />
        </button>
        {menuOpen && (
          <div style={{
            position: 'absolute', top: 32, left: 0, zIndex: 20,
            background: 'var(--surface-2)', border: '1px solid var(--line)',
            borderRadius: 8, padding: 4,
            minWidth: 260,
            boxShadow: 'var(--shadow-panel)',
          }}>
            {accounts.map(acc => (
              <div key={acc.id} style={{ padding: '6px 8px 2px' }}>
                <div className="mono" style={{
                  fontSize: 9.5, letterSpacing: 0.6, textTransform: 'uppercase',
                  color: 'var(--muted)',
                }}>
                  {acc.provider} · {acc.label}
                </div>
                {acc.calendars.filter(c => c.role !== 'reader').map(cal => {
                  const isSel = linkedId === cal.id;
                  return (
                    <button key={cal.id}
                      onClick={() => { onSetCardCalendar(card.id, isSel ? null : cal.id); setMenuOpen(false); }}
                      style={{
                        width: '100%', textAlign: 'left',
                        display: 'flex', alignItems: 'center', gap: 8,
                        padding: '6px 8px', borderRadius: 6,
                        background: isSel ? 'var(--line-soft)' : 'transparent',
                        fontSize: 12, color: 'var(--ink)',
                      }}>
                      <span style={{
                        width: 10, height: 10, borderRadius: 2, background: cal.color,
                      }} />
                      <span style={{ flex: 1 }}>{cal.name}</span>
                      {targets.personal === cal.id && (
                        <span className="mono" style={{ fontSize: 9, color: 'var(--muted)' }}>personal</span>
                      )}
                      {targets.shared === cal.id && (
                        <span className="mono" style={{ fontSize: 9, color: 'var(--muted)' }}>shared</span>
                      )}
                      {isSel && <Icon name="check" size={12} stroke={2} />}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        )}
      </div>

      {linked && (
        <div className="mono" style={{ fontSize: 10.5, color: 'var(--muted)' }}>
          event_id: {card.calendarEvent.eventId}
          {isOnShared && ' · visible to family'}
        </div>
      )}
    </div>
  );
};

const Field = ({ label, children, hint }) => (
  <div style={{ marginBottom: 18 }}>
    <div className="mono" style={{
      fontSize: 10, letterSpacing: 0.8, textTransform: 'uppercase',
      color: 'var(--muted)', marginBottom: 6,
    }}>{label}{hint && <span style={{ marginLeft: 6, textTransform: 'none', letterSpacing: 0, color: 'var(--muted)', opacity: 0.7 }}>{hint}</span>}</div>
    {children}
  </div>
);

const HistoryRow = ({ entry, today }) => {
  const date = new Date(entry.ts);
  const diff = daysBetween(date, today);
  const rel = diff === 0 ? 'today' : diff === 1 ? 'yesterday' : `${diff}d ago`;
  const timeStr = `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
  const meta = {
    created: { icon: 'sparkle', color: 'var(--violet)', text: () => <span>Created</span> },
    moved:   { icon: 'arrow_r', color: 'var(--navy)',   text: (e) => <span>Moved <strong>{e.from}</strong> → <strong>{e.to}</strong></span> },
    edited:  { icon: 'edit',    color: 'var(--amber)',  text: (e) => <span>Edited <strong>{e.field}</strong></span> },
    done:    { icon: 'check',   color: 'var(--olive)',  text: () => <span>Completed</span> },
    reopened:{ icon: 'history', color: 'var(--muted)',  text: () => <span>Reopened</span> },
    scheduled:{ icon: 'cal',    color: 'var(--olive)',  text: (e) => <span>{e.toValue ? 'Linked to Calendar' : 'Unlinked from Calendar'}</span> },
  }[entry.type] || { icon: 'dot', color: 'var(--muted)', text: () => <span>{entry.type}</span> };

  return (
    <div style={{ display: 'flex', gap: 10, padding: '6px 0', alignItems: 'flex-start' }}>
      <div style={{
        width: 22, height: 22, borderRadius: 999, flexShrink: 0,
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--surface)', border: '1px solid var(--line)', color: meta.color,
        marginTop: 1,
      }}>
        <Icon name={meta.icon} size={12} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, color: 'var(--ink)', lineHeight: 1.35 }}>{meta.text(entry)}</div>
        <div className="mono" style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 1 }}>
          {rel} · {timeStr}
        </div>
      </div>
    </div>
  );
};

const Detail = ({ card, today, categories, categoryOrder, accounts, targets, onClose, onChange, onToggleDone, onDelete, onSetCardCalendar }) => {
  const titleRef = React.useRef(null);
  const [descDraft, setDescDraft] = React.useState(card?.description || '');
  const [titleDraft, setTitleDraft] = React.useState(card?.title || '');

  React.useEffect(() => {
    setDescDraft(card?.description || '');
    setTitleDraft(card?.title || '');
  }, [card?.id]);

  if (!card) return null;
  const pri = PRIORITIES[card.priority];
  const age = daysBetween(startOfDay(card.createdAt), today);

  const commitTitle = () => {
    if (titleDraft.trim() && titleDraft !== card.title) {
      onChange(card.id, { title: titleDraft.trim() }, 'title');
    } else {
      setTitleDraft(card.title);
    }
  };
  const commitDesc = () => {
    if (descDraft !== card.description) {
      onChange(card.id, { description: descDraft }, 'description');
    }
  };

  return (
    <aside style={{
      position: 'absolute', top: 0, right: 0, bottom: 0,
      width: 440, background: 'var(--surface)',
      borderLeft: '1px solid var(--line)',
      boxShadow: 'var(--shadow-panel)',
      display: 'flex', flexDirection: 'column',
      zIndex: 10,
    }}>
      {/* header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px', borderBottom: '1px solid var(--line)',
      }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={() => onToggleDone(card.id)}
            style={{
              width: 18, height: 18,
              border: `1.5px solid ${card.done ? pri.color : 'var(--line)'}`,
              background: card.done ? pri.color : 'transparent',
              borderRadius: 4, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff',
            }}>
            {card.done && <Icon name="check" size={12} stroke={2.2} />}
          </button>
          <span className="mono" style={{ fontSize: 11, color: 'var(--muted)' }}>
            {card.id.toUpperCase()} · created {age === 0 ? 'today' : `${age}d ago`}
          </span>
        </div>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <button onClick={() => onDelete(card.id)} title="Delete"
            style={{ width: 28, height: 28, borderRadius: 6, color: 'var(--muted)',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--coral-soft)'; e.currentTarget.style.color = 'var(--coral)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--muted)'; }}>
            <Icon name="x" size={14} />
          </button>
          <button onClick={onClose} title="Close (esc)"
            style={{ width: 28, height: 28, borderRadius: 6, color: 'var(--muted)',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--line-soft)'; e.currentTarget.style.color = 'var(--ink)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--muted)'; }}>
            <Icon name="chev_r" size={14} />
          </button>
        </div>
      </div>

      {/* scroll body */}
      <div style={{ flex: 1, overflow: 'auto', padding: '18px 20px 30px' }}>
        <textarea
          ref={titleRef}
          value={titleDraft}
          onChange={(e) => setTitleDraft(e.target.value)}
          onBlur={commitTitle}
          rows={1}
          placeholder="Task title"
          style={{
            width: '100%', resize: 'none', border: 0, background: 'transparent',
            fontFamily: 'inherit', fontSize: 22, fontWeight: 600, lineHeight: 1.25,
            padding: 0, color: 'var(--ink)',
            textDecoration: card.done ? 'line-through' : 'none',
            opacity: card.done ? 0.55 : 1,
            overflow: 'hidden',
          }}
          onInput={(e) => { e.target.style.height = 'auto'; e.target.style.height = e.target.scrollHeight + 'px'; }}
        />

        <div style={{ marginTop: 16 }} />

        <Field label="Description" hint="markdown welcome">
          <textarea
            value={descDraft}
            onChange={(e) => setDescDraft(e.target.value)}
            onBlur={commitDesc}
            placeholder="What does done look like? Links, acceptance criteria, context…"
            rows={5}
            style={{
              width: '100%', resize: 'vertical',
              background: 'var(--surface-2)', border: '1px solid var(--line)',
              borderRadius: 8, padding: '10px 12px',
              fontFamily: 'inherit', fontSize: 13, lineHeight: 1.5, color: 'var(--ink)',
              minHeight: 96,
            }}
          />
        </Field>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
          <Field label="Priority">
            <PriorityPicker value={card.priority} onChange={(v) => onChange(card.id, { priority: v }, 'priority')} />
          </Field>
          <Field label="Size">
            <SizePicker value={card.size} onChange={(v) => onChange(card.id, { size: v, estimateMinutes: SIZES[v].minutes }, 'size')} />
          </Field>
        </div>

        <Field label="Category">
          <CategoryPicker
            value={card.category}
            order={categoryOrder}
            categories={categories}
            onChange={(v) => onChange(card.id, { category: v }, 'category')}
          />
        </Field>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
          <Field label="Estimated time" hint="override size default">
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <input
                type="number" min="0" step="5"
                value={card.estimateMinutes ?? ''}
                onChange={(e) => onChange(card.id, { estimateMinutes: e.target.value === '' ? null : Math.max(0, parseInt(e.target.value, 10) || 0) }, 'estimate')}
                style={{
                  width: 78, padding: '6px 10px',
                  border: '1px solid var(--line)', borderRadius: 6,
                  background: 'var(--surface-2)', fontFamily: 'Geist Mono, monospace', fontSize: 13,
                }}
              />
              <span className="mono" style={{ fontSize: 12, color: 'var(--muted)' }}>min</span>
              <span style={{ marginLeft: 8, color: 'var(--muted)', fontSize: 12 }}>
                {card.estimateMinutes != null && fmtMinutes(card.estimateMinutes)}
              </span>
            </div>
          </Field>
          <Field label="Target time" hint="optional, time of day">
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <input
                type="time"
                value={card.timeOfDay || ''}
                onChange={(e) => onChange(card.id, { timeOfDay: e.target.value || null }, 'time')}
                style={{
                  padding: '6px 10px', border: '1px solid var(--line)', borderRadius: 6,
                  background: 'var(--surface-2)', fontFamily: 'Geist Mono, monospace', fontSize: 13,
                }}
              />
              {card.timeOfDay && (
                <button onClick={() => onChange(card.id, { timeOfDay: null }, 'time')}
                  style={{ color: 'var(--muted)', padding: 4 }} title="Clear">
                  <Icon name="x" size={12} />
                </button>
              )}
            </div>
          </Field>
        </div>

        <Field label="Calendar" hint="where this task lives in your calendar app">
          <CalendarChooser
            card={card}
            accounts={accounts}
            targets={targets}
            onSetCardCalendar={onSetCardCalendar}
          />
        </Field>

        {/* Activity */}
        <Field label={`Activity · ${card.history.length} event${card.history.length === 1 ? '' : 's'}`}>
          <div style={{
            background: 'var(--surface-2)', border: '1px solid var(--line)', borderRadius: 8,
            padding: '4px 12px',
          }}>
            {[...card.history].reverse().map((entry, i) => (
              <HistoryRow key={i} entry={entry} today={today} />
            ))}
          </div>
        </Field>

        {/* counters summary */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8,
          padding: 12, background: 'var(--surface-2)', border: '1px solid var(--line)', borderRadius: 8,
        }}>
          {[
            { label: 'Age', value: age === 0 ? '<1d' : `${age}d` },
            { label: 'Moves', value: card.moveCount },
            { label: 'Edits', value: card.editCount },
            { label: 'Status', value: card.done ? 'Done' : 'Open' },
          ].map(s => (
            <div key={s.label}>
              <div className="mono" style={{ fontSize: 9.5, letterSpacing: 0.8, textTransform: 'uppercase', color: 'var(--muted)' }}>{s.label}</div>
              <div className="mono" style={{ fontSize: 16, fontWeight: 500, marginTop: 2 }}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};

window.Detail = Detail;
