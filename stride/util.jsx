// util.jsx — date helpers, constants, tiny components shared across files

const TODAY = new Date(2026, 4, 12); // May 12, 2026 — locked for the demo so dates stay consistent

const DAY_MS = 86400000;
const startOfDay = (d) => { const x = new Date(d); x.setHours(0,0,0,0); return x; };
const addDays = (d, n) => new Date(startOfDay(d).getTime() + n * DAY_MS);
const dayKey = (d) => {
  const x = startOfDay(d);
  return `${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,'0')}-${String(x.getDate()).padStart(2,'0')}`;
};
const parseKey = (k) => {
  const [y, m, d] = k.split('-').map(Number);
  return new Date(y, m - 1, d);
};
const daysBetween = (a, b) => Math.round((startOfDay(b) - startOfDay(a)) / DAY_MS);

const WEEKDAY_LONG = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const WEEKDAY_SHORT = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const MONTH_SHORT = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const dayLabel = (d, today) => {
  const diff = daysBetween(today, d);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  if (diff === -1) return 'Yesterday';
  return WEEKDAY_LONG[d.getDay()];
};

// Size scale: rough effort. Times are *defaults*; the user can override per-card.
const SIZES = {
  XS: { label: 'XS', minutes: 10, hint: '<15m' },
  S:  { label: 'S',  minutes: 25, hint: '~25m' },
  M:  { label: 'M',  minutes: 60, hint: '~1h'  },
  L:  { label: 'L',  minutes: 120, hint: '~2h'  },
  XL: { label: 'XL', minutes: 240, hint: 'half day' },
};
const SIZE_ORDER = ['XS','S','M','L','XL'];

const PRIORITIES = {
  P1: { label: 'P1', name: 'Critical', color: 'var(--coral)',  bg: 'var(--coral-soft)' },
  P2: { label: 'P2', name: 'High',     color: 'var(--amber)',  bg: 'var(--amber-soft)' },
  P3: { label: 'P3', name: 'Normal',   color: 'var(--navy)',   bg: 'var(--navy-soft)'  },
  P4: { label: 'P4', name: 'Low',      color: 'var(--muted)',  bg: 'var(--line-soft)'  },
};
const PRIORITY_ORDER = ['P1','P2','P3','P4'];

// Categories — a different axis from priority. The user owns these via Tweaks.
// Cards reference by id; names + colors are tweakable.
const DEFAULT_CATEGORY_ORDER = ['build', 'work', 'home', 'admin', 'health', 'personal'];

// Curated palette for category swatch picker. OKLCH-balanced muted hues.
const CATEGORY_COLOR_PALETTE = [
  '#6a4ea3', // violet
  '#2a4a7f', // navy
  '#4f7a3b', // olive
  '#c98521', // amber
  '#d94a5e', // coral
  '#2d8f8b', // teal
  '#8a4a2a', // rust
  '#3a6b8e', // slate-blue
  '#6e7a35', // lime-olive
  '#a5547e', // mauve
  '#5b6b7f', // slate
  '#1f5d4a', // forest
];

const fmtMinutes = (m) => {
  if (m == null) return '';
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60), r = m % 60;
  return r === 0 ? `${h}h` : `${h}h ${r}m`;
};

const fmtTime = (hhmm) => {
  if (!hhmm) return '';
  const [h, m] = hhmm.split(':').map(Number);
  const period = h >= 12 ? 'pm' : 'am';
  const h12 = ((h + 11) % 12) + 1;
  return m === 0 ? `${h12}${period}` : `${h12}:${String(m).padStart(2,'0')}${period}`;
};

// ID
let _idCounter = 1000;
const uid = () => `c${++_idCounter}`;

// Icons — sized via CSS, all 16px viewport
const Icon = ({ name, size = 14, stroke = 1.6, style }) => {
  const paths = {
    check:    <polyline points="3.5 8 6.5 11 12.5 5" />,
    plus:     <g><line x1="8" y1="3" x2="8" y2="13" /><line x1="3" y1="8" x2="13" y2="8" /></g>,
    x:        <g><line x1="4" y1="4" x2="12" y2="12" /><line x1="12" y1="4" x2="4" y2="12" /></g>,
    chev_l:   <polyline points="10 3 5 8 10 13" />,
    chev_r:   <polyline points="6 3 11 8 6 13" />,
    chev_d:   <polyline points="3 6 8 11 13 6" />,
    edit:     <g><path d="M3 13l2-0.5 7-7-1.5-1.5-7 7L3 13z" /><line x1="9.5" y1="4" x2="12" y2="6.5" /></g>,
    move:     <g><path d="M3 8h10" /><polyline points="10 5 13 8 10 11" /></g>,
    repeat:   <g><polyline points="4 4 4 7 7 7" /><path d="M4 7a5 5 0 0 1 8.5-2" /><polyline points="12 12 12 9 9 9" /><path d="M12 9a5 5 0 0 1-8.5 2" /></g>,
    cal:      <g><rect x="2.5" y="3.5" width="11" height="10" rx="1.2" /><line x1="2.5" y1="6.5" x2="13.5" y2="6.5" /><line x1="5.5" y1="2.5" x2="5.5" y2="4.5" /><line x1="10.5" y1="2.5" x2="10.5" y2="4.5" /></g>,
    clock:    <g><circle cx="8" cy="8" r="5.5" /><polyline points="8 5 8 8 10 9.5" /></g>,
    flag:     <g><path d="M4 13V3" /><path d="M4 3 H11 L9.5 5.5 L11 8 H4" /></g>,
    sparkle:  <path d="M8 2 L9 6.5 L13.5 7.5 L9 8.5 L8 13 L7 8.5 L2.5 7.5 L7 6.5 Z" />,
    dot:      <circle cx="8" cy="8" r="2.5" />,
    search:   <g><circle cx="7" cy="7" r="4" /><line x1="10" y1="10" x2="13" y2="13" /></g>,
    filter:   <g><path d="M3 4h10l-4 5v4l-2 1V9z" /></g>,
    inbox:    <g><path d="M3 9l1.5-5h7L13 9" /><path d="M3 9v3.5h10V9h-3l-1 1.5h-2L6 9H3z" /></g>,
    settings: <g><circle cx="8" cy="8" r="2" /><path d="M8 2v1.5M8 12.5V14M14 8h-1.5M3.5 8H2M12.2 3.8l-1 1M4.8 11.2l-1 1M12.2 12.2l-1-1M4.8 4.8l-1-1" /></g>,
    arrow_r:  <g><line x1="3" y1="8" x2="12" y2="8" /><polyline points="9 5 12 8 9 11" /></g>,
    history:  <g><path d="M3 8a5 5 0 1 0 1.5-3.5" /><polyline points="3 2.5 3 5 5.5 5" /><polyline points="8 5 8 8 10.5 9.5" /></g>,
    note:     <g><path d="M4 3h6l3 3v7H4z" /><polyline points="10 3 10 6 13 6" /></g>,
    drag:     <g><circle cx="6" cy="4" r="1" /><circle cx="10" cy="4" r="1" /><circle cx="6" cy="8" r="1" /><circle cx="10" cy="8" r="1" /><circle cx="6" cy="12" r="1" /><circle cx="10" cy="12" r="1" /></g>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor"
         strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" style={style} aria-hidden>
      {paths[name]}
    </svg>
  );
};

// A tiny chip for metadata, used widely
const Chip = ({ children, color, bg, border, mono, title, onClick, style }) => {
  const isButton = !!onClick;
  const Tag = isButton ? 'button' : 'span';
  return (
    <Tag
      title={title}
      onClick={onClick}
      className={mono ? 'mono' : ''}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 6px',
        height: 20,
        borderRadius: 6,
        fontSize: 11,
        fontWeight: 500,
        letterSpacing: 0.1,
        color: color || 'var(--ink-2)',
        background: bg || 'transparent',
        border: border ? `1px solid ${border}` : '1px solid var(--line-soft)',
        cursor: isButton ? 'pointer' : 'default',
        whiteSpace: 'nowrap',
        ...style,
      }}
    >
      {children}
    </Tag>
  );
};

Object.assign(window, {
  TODAY, DAY_MS, startOfDay, addDays, dayKey, parseKey, daysBetween,
  WEEKDAY_LONG, WEEKDAY_SHORT, MONTH_SHORT, dayLabel,
  SIZES, SIZE_ORDER, PRIORITIES, PRIORITY_ORDER,
  DEFAULT_CATEGORY_ORDER, CATEGORY_COLOR_PALETTE,
  fmtMinutes, fmtTime, uid,
  Icon, Chip,
});
