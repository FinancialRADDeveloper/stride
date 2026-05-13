"""Stride colour tokens and Mantine theme configuration."""

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

COLOUR_BG = "#f5f3ee"         # warm cream background
COLOUR_SURFACE = "#ffffff"    # card background
COLOUR_TEXT = "#1a1a1a"       # text primary
COLOUR_MUTED = "#6b7280"      # text muted
COLOUR_BORDER = "#e5e7eb"     # border

# Priority colours
PRIORITY_COLOURS = {
    "P1": "#ef4444",
    "P2": "#f59e0b",
    "P3": "#6366f1",
    "P4": "#9ca3af",
}

# Category colours — must match the SQL seed in 0001_init.sql
CATEGORY_COLOURS = {
    "build":    "#6366f1",
    "work":     "#0ea5e9",
    "home":     "#22c55e",
    "admin":    "#f59e0b",
    "health":   "#ef4444",
    "personal": "#a855f7",
}

# Capacity bar thresholds
CAPACITY_OK_COLOUR = "#22c55e"
CAPACITY_WARN_COLOUR = "#f59e0b"
CAPACITY_OVER_COLOUR = "#ef4444"

# ---------------------------------------------------------------------------
# Mantine theme dict
# ---------------------------------------------------------------------------

STRIDE_THEME = {
    "fontFamily": "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "primaryColor": "indigo",
    "defaultRadius": "md",
    "colors": {
        "brand": [
            "#f5f3ee",
            "#ede9e0",
            "#ddd8cc",
            "#c9c2b0",
            "#b4aa94",
            "#9c9278",
            "#817860",
            "#665f4c",
            "#4d4738",
            "#333026",
        ],
    },
}
