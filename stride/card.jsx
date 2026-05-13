// card.jsx — task card surface

const Card = ({ card, today, categories, calendarsById, isDragging, isSelected, onSelect, onToggleDone, onDragStart, onDragEnd, showStaleRibbon = true }) => {
  const pri = PRIORITIES[card.priority];
  const sz = SIZES[card.size];
  const cat = categories[card.category] || { name: '—', color: 'var(--muted)' };
  const age = daysBetween(startOfDay(card.createdAt), today);
  const isStale = card.moveCount >= 3 && !card.done;
  const linkedCal = card.calendarEvent
    ? (calendarsById?.[card.calendarEvent.calendarId] || null)
    : null;
  const scheduled = !!card.calendarEvent;

  return (
    <div
      draggable={!card.done}
      onDragStart={(e) => { e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', card.id); onDragStart && onDragStart(card.id); }}
      onDragEnd={() => onDragEnd && onDragEnd()}
      onClick={() => onSelect(card.id)}
      style={{
        position: 'relative',
        background: 'var(--surface-2)',
        borderRadius: 'var(--radius-card)',
        border: isSelected ? '1px solid var(--ink)' : '1px solid var(--line)',
        boxShadow: isSelected ? 'var(--shadow-card-hover)' : 'var(--shadow-card)',
        opacity: isDragging ? 0.35 : (card.done ? 0.55 : 1),
        cursor: 'grab',
        padding: '10px 12px 10px 12px',
        transition: 'box-shadow 120ms ease, transform 120ms ease, border-color 120ms ease',
        userSelect: 'none',
      }}
      onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.boxShadow = 'var(--shadow-card-hover)'; }}
      onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.boxShadow = 'var(--shadow-card)'; }}
    >
      {/* category stripe on the left */}
      <div title={cat.name} style={{
        position: 'absolute', left: 0, top: 8, bottom: 8, width: 3,
        background: cat.color, borderRadius: '0 2px 2px 0',
      }} />

      {/* stale ribbon — only when moved a lot */}
      {isStale && showStaleRibbon && (
        <div title={`Moved ${card.moveCount} times — consider breaking it down or dropping it`}
          style={{
            position: 'absolute', top: -6, right: 10,
            background: 'var(--amber-soft)', color: 'var(--amber)',
            border: '1px solid var(--amber)',
            borderRadius: 4, padding: '1px 5px', fontSize: 10, fontWeight: 600,
            letterSpacing: 0.3, textTransform: 'uppercase',
          }} className="mono">stale</div>
      )}

      {/* top row: checkbox + title */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginLeft: 2 }}>
        <button
          onClick={(e) => { e.stopPropagation(); onToggleDone(card.id); }}
          aria-label={card.done ? 'Reopen task' : 'Complete task'}
          style={{
            width: 16, height: 16, marginTop: 1, flex: '0 0 16px',
            border: `1.5px solid ${card.done ? pri.color : 'var(--line)'}`,
            background: card.done ? pri.color : 'transparent',
            borderRadius: 4, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff',
          }}>
          {card.done && <Icon name="check" size={11} stroke={2.2} />}
        </button>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{
            fontWeight: 500, lineHeight: 1.3, fontSize: 13.5,
            color: card.done ? 'var(--muted)' : 'var(--ink)',
            textDecoration: card.done ? 'line-through' : 'none',
            wordBreak: 'break-word',
          }}>{card.title}</div>
          {card.description && (
            <div style={{
              marginTop: 3, fontSize: 12, color: 'var(--muted)', lineHeight: 1.35,
              display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
              overflow: 'hidden', textOverflow: 'ellipsis',
            }}>{card.description}</div>
          )}
        </div>
      </div>

      {/* bottom row: metadata chips + history glyphs */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 4, marginTop: 8, marginLeft: 24,
        flexWrap: 'wrap',
      }}>
        <Chip color={pri.color} bg={pri.bg} border="transparent" title={`${pri.name} priority`}>
          <span style={{ width: 6, height: 6, borderRadius: 999, background: pri.color, display: 'inline-block' }} />
          <span className="mono" style={{ fontSize: 10.5 }}>{pri.label}</span>
        </Chip>
        <Chip mono title={`Size: ${sz.label} (${sz.hint})`}>{sz.label}</Chip>
        {card.estimateMinutes != null && (
          <Chip mono title="Estimated time">
            <Icon name="clock" size={10} stroke={1.8} /> {fmtMinutes(card.estimateMinutes)}
          </Chip>
        )}
        {card.timeOfDay && (
          <Chip mono title="Scheduled time of day"
            color="var(--navy)" bg="var(--navy-soft)" border="transparent">
            {fmtTime(card.timeOfDay)}
          </Chip>
        )}
        {scheduled && (
          <Chip
            color={linkedCal ? linkedCal.color : 'var(--olive)'}
            bg="transparent"
            border={linkedCal ? linkedCal.color : 'var(--olive)'}
            title={linkedCal ? `On ${linkedCal.name}` : 'On Calendar'}
            style={{ background: linkedCal ? `${linkedCal.color}14` : 'var(--olive-soft)' }}
          >
            <span style={{
              width: 6, height: 6, borderRadius: 1.5,
              background: linkedCal ? linkedCal.color : 'var(--olive)',
            }} />
            <span style={{ fontSize: 10.5 }}>{linkedCal ? linkedCal.name : 'GCal'}</span>
          </Chip>
        )}

        {/* push history glyphs to the right */}
        <div style={{ flex: 1 }} />

        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--muted)' }}>
          {card.editCount > 0 && (
            <span title={`${card.editCount} edit${card.editCount > 1 ? 's' : ''}`} style={{ display: 'inline-flex' }}>
              <Icon name="edit" size={11} stroke={1.6} />
            </span>
          )}
          {card.moveCount > 0 && (
            <span title={`Moved ${card.moveCount} time${card.moveCount > 1 ? 's' : ''}`}
              className="mono" style={{ display: 'inline-flex', alignItems: 'center', gap: 2, fontSize: 10.5 }}>
              <Icon name="repeat" size={11} stroke={1.6} />{card.moveCount}
            </span>
          )}
          {age > 0 && (
            <span title={`Created ${age} day${age > 1 ? 's' : ''} ago`}
              className="mono"
              style={{ fontSize: 10.5, color: age >= 7 ? 'var(--coral)' : 'var(--muted)', fontWeight: age >= 7 ? 600 : 400 }}>
              {age}d
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

window.Card = Card;
