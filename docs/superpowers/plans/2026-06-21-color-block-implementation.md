# Color-Block 多彩分区块 Implementation Plan

> **For agentic workers:** This plan has a single task — add CSS variables and color classes across 4 pages. All changes are additive (no layout or logic modifications).

**Goal:** Apply color-block styling across Dashboard, Usage, and Keys pages using the approved color mapping.

**Architecture:** Add 10 CSS variables to `base.css`, then apply per-page: wrap stat card groups in color class containers, add inline styles for left border and background.

**Tech Stack:** Vue 3, existing CSS variables.

---

### Task 1: Add CSS variables + update pages

- [ ] **Step 1: Add CSS variables to `base.css`**

In `frontend/src/styles/base.css`, inside `:root`, after existing `--page-bg`, add:

```css
  /* Color-block card backgrounds */
  --card-blue-bg: #eef2ff;
  --card-blue-accent: #4f6ef7;
  --card-green-bg: #ecfdf5;
  --card-green-accent: #34d399;
  --card-purple-bg: #faf5ff;
  --card-purple-accent: #a855f7;
  --card-yellow-bg: #fefce8;
  --card-yellow-accent: #f59e0b;
  --card-red-bg: #fef2f2;
  --card-red-accent: #dc2626;
```

- [ ] **Step 2: Update Dashboard.vue stat cards**

Wrap the 4 summary stat cards. Change each `dash-stat-card` div to include `:style`:

First card (balance → blue):
```html
<div class="dash-stat-card" style="background:var(--card-blue-bg);border-left:3px solid var(--card-blue-accent)">
```

Second card (requests → green):
```html
<div class="dash-stat-card" style="background:var(--card-green-bg);border-left:3px solid var(--card-green-accent)">
```

Third card (tokens → purple):
```html
<div class="dash-stat-card" style="background:var(--card-purple-bg);border-left:3px solid var(--card-purple-accent)">
```

Fourth card (keys → yellow):
```html
<div class="dash-stat-card" style="background:var(--card-yellow-bg);border-left:3px solid var(--card-yellow-accent)">
```

Also update chart card headers — change `.dash-section-title` to `style="color:..."`. For the cost chart: `color:var(--card-blue-accent)`, for token chart: `color:var(--card-green-accent)`.

- [ ] **Step 3: Update Usage.vue stat cards**

First card (cost → yellow):
```html
<div class="stat-card-item" style="background:var(--card-yellow-bg);border-left:3px solid var(--card-yellow-accent)">
```

Second card (calls → blue):
```html
<div class="stat-card-item" style="background:var(--card-blue-bg);border-left:3px solid var(--card-blue-accent)">
```

Third card (tokens → purple):
```html
<div class="stat-card-item" style="background:var(--card-purple-bg);border-left:3px solid var(--card-purple-accent)">
```

Fourth card (error → red):
```html
<div class="stat-card-item" style="background:var(--card-red-bg);border-left:3px solid var(--card-red-accent)">
```

- [ ] **Step 4: Update Keys.vue summary cards**

First card (keys total → blue):
```html
<div class="key-summary-card" style="background:var(--card-blue-bg);border-left:3px solid var(--card-blue-accent)">
```

Second card (active → green):
```html
<div class="key-summary-card" style="background:var(--card-green-bg);border-left:3px solid var(--card-green-accent)">
```

Third card (month calls → purple):
```html
<div class="key-summary-card" style="background:var(--card-purple-bg);border-left:3px solid var(--card-purple-accent)">
```

API info card (→ purple):
```html
<div class="key-api-card" style="background:var(--card-purple-bg);border-left:3px solid var(--card-purple-accent)">
```

- [ ] **Step 5: Verify in browser**

Navigate to http://localhost:5173/ and check:
1. Dashboard 4 stat cards: blue / green / purple / yellow backgrounds
2. Dashboard 2 chart titles: blue and green
3. Usage 4 stat cards: yellow / blue / purple / red
4. Keys 3 summary cards: blue / green / purple
5. Keys API info card: purple background
6. All layouts and data intact
