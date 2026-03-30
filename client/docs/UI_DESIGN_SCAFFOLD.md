# Visual AOI Client - UI Design Scaffold & Guidelines

**Version:** 2.0  
**Date:** October 3, 2025  
**Status:** Living Document

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Color System](#color-system)
3. [Component Library](#component-library)
4. [Layout Structure](#layout-structure)
5. [Typography](#typography)
6. [Iconography](#iconography)
7. [Interactive States](#interactive-states)
8. [Animation Guidelines](#animation-guidelines)
9. [Responsive Behavior](#responsive-behavior)
10. [Code Templates](#code-templates)

---

## Design Philosophy

### Core Principles

**1. iOS-Inspired Professional Aesthetic**
- Clean, minimal interface with purposeful white space
- Glass morphism effects for depth and hierarchy
- Subtle shadows and gradients
- High contrast for readability

**2. Industrial Application Focus**
- Clear status indicators at all times
- Immediate visual feedback for all actions
- Error states prominently displayed
- Safety-critical information highlighted

**3. Operator-Centric Design**
- Large, touch-friendly buttons (minimum 44px)
- Consistent placement of primary actions
- Progressive disclosure of complexity
- Quick access to common tasks

**4. Data Density Balance**
- Summary information always visible
- Detailed data available on demand
- Collapsible sections for space management
- Intelligent defaults for new users

---

## Color System

### Theme Architecture

The application supports **Light** and **Dark** themes with automatic switching.

#### Light Theme (Default)
```css
:root {
    /* Backgrounds */
    --bg: #F2F2F7;              /* Page background */
    --secondary-bg: #FFFFFF;     /* Card background */
    --tertiary-bg: #F8F8F8;      /* Nested elements */
    --surface: #FFFFFF;          /* Elevated surfaces */

    /* Glass Effects */
    --glass-bg: #FFFFFF;
    --glass-surface: #F8F8F8;
    --glass-surface-hover: #F0F0F0;
    --glass-border: #E0E0E0;
    --glass-highlight: #E8E8E8;
    --glass-shadow: #F5F5F5;
    --glass-backdrop: #F2F2F7;

    /* Text */
    --fg: #000000;              /* Primary text */
    --secondary-fg: #3C3C43;    /* Secondary text */
    --tertiary-fg: #8E8E93;     /* Disabled/hint text */
    --placeholder-fg: #C7C7CC;  /* Placeholder text */

    /* Accent Colors */
    --primary: #007AFF;         /* Primary actions */
    --primary-light: #34C759;   /* Success variant */
    --primary-dark: #005BBB;    /* Active state */

    /* Status Colors */
    --success: #34C759;         /* Pass, success */
    --warning: #FF9500;         /* Warning, medium priority */
    --error: #FF3B30;           /* Fail, critical */
    --info: #007AFF;            /* Information, neutral */

    /* Interactive */
    --button-bg: #007AFF;
    --button-fg: #FFFFFF;
    --button-secondary: #F2F2F7;
    --button-secondary-fg: #007AFF;
    --button-active: #005BBB;

    /* Form Elements */
    --input-bg: #FFFFFF;
    --input-fg: #000000;
    --input-border: #D1D1D6;
    --input-border-focus: #007AFF;

    /* Selection */
    --select-bg: #007AFF;
    --select-fg: #FFFFFF;
}
```

#### Dark Theme
```css
[data-theme="dark"] {
    /* Backgrounds */
    --bg: #000000;
    --secondary-bg: #1C1C1E;
    --tertiary-bg: #2C2C2E;
    --surface: #1C1C1E;

    /* Glass Effects */
    --glass-bg: rgba(28, 28, 30, 0.95);
    --glass-surface: rgba(44, 44, 46, 0.9);
    --glass-surface-hover: rgba(58, 58, 60, 0.9);
    --glass-border: rgba(84, 84, 88, 0.5);
    --glass-highlight: rgba(72, 72, 74, 0.8);
    --glass-shadow: rgba(0, 0, 0, 0.3);
    --glass-backdrop: rgba(0, 0, 0, 0.4);

    /* Text */
    --fg: #FFFFFF;
    --secondary-fg: #EBEBF5;
    --tertiary-fg: #8E8E93;
    --placeholder-fg: #48484A;

    /* Status Colors (adjusted for dark) */
    --success: #30D158;
    --warning: #FF9F0A;
    --error: #FF453A;
    --info: #0A84FF;

    /* Other colors remain similar but adjusted for contrast */
}
```

### Color Usage Guidelines

#### Visual Color Hierarchy
```
Status Indicators (Semantic Colors):
┌─────────────────────────────────────────────────────────┐
│  ✓ PASS    │ ● Connected    │ ✓ Active    │ #34C759   │  Green
├─────────────────────────────────────────────────────────┤
│  ✗ FAIL    │ ● Disconnected │ ✗ Error     │ #FF3B30   │  Red
├─────────────────────────────────────────────────────────┤
│  ⚠ Warning │ ● Partial      │ ⚠ Medium    │ #FF9500   │  Orange
├─────────────────────────────────────────────────────────┤
│  ℹ Info    │ ● Processing   │ ℹ Neutral   │ #007AFF   │  Blue
└─────────────────────────────────────────────────────────┘

Type Badges (ROI Types):
┌─────────────────────────────────────────────────────────┐
│  [BARCODE]    │  Barcode detection       │  #007AFF   │  Blue
├─────────────────────────────────────────────────────────┤
│  [OCR]        │  Text recognition        │  #5856D6   │  Purple
├─────────────────────────────────────────────────────────┤
│  [COMPARE]    │  Image comparison        │  #FF9500   │  Orange
├─────────────────────────────────────────────────────────┤
│  [TEXT]       │  Text matching           │  #AF52DE   │  Magenta
└─────────────────────────────────────────────────────────┘

Similarity Bars (AI Confidence):
┌─────────────────────────────────────────────────────────┐
│  ████████████████████  ≥80%   High        │  #34C759   │  Green
├─────────────────────────────────────────────────────────┤
│  ████████████░░░░░░░░  60-79% Medium      │  #FF9500   │  Orange
├─────────────────────────────────────────────────────────┤
│  ██████░░░░░░░░░░░░░░  <60%   Low         │  #FF3B30   │  Red
└─────────────────────────────────────────────────────────┘
```

**Status Indicators:**
- ✅ **Green** (`--success`): PASS, connected, active, success
- ❌ **Red** (`--error`): FAIL, disconnected, error, critical
- ⚠️ **Orange** (`--warning`): Warning, partial, medium priority
- ℹ️ **Blue** (`--info`): Information, neutral, processing

**Type Badges:**
- 🔵 **Blue** (`#007AFF`): Barcode ROIs
- 🟣 **Purple** (`#5856D6`): OCR ROIs
- 🟠 **Orange** (`#FF9500`): Compare ROIs
- 🟣 **Magenta** (`#AF52DE`): Text ROIs

**Semantic Colors:**
```css
/* Never use raw hex colors in components */
/* ❌ Bad */
.button { background: #007AFF; }

/* ✅ Good */
.button { background: var(--primary); }
```

---

## Component Library

### 1. Buttons

#### Visual Structure
```
┌─────────────────────────────┐
│                             │
│     Primary Action  ←──── Text (--button-fg)
│                             │
└─────────────────────────────┘
  ↑                         ↑
  Background               Border Radius: 10px
  (--button-bg)            Shadow on hover
```

#### Glass Button (Primary)
```html
<button class="glass-button">Primary Action</button>
```
```css
.glass-button {
    background: var(--button-bg);
    color: var(--button-fg);
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0, 122, 255, 0.2);
}

.glass-button:hover {
    background: var(--button-active);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 122, 255, 0.3);
}

.glass-button:active {
    transform: translateY(0);
}
```

#### Variants
```html
<!-- Secondary -->
<button class="glass-button secondary">Secondary</button>

<!-- Success -->
<button class="glass-button success">Success</button>

<!-- Danger -->
<button class="glass-button danger">Danger</button>

<!-- Disabled -->
<button class="glass-button" disabled>Disabled</button>
```

### 2. Sections

#### Visual Structure
```
┌─────────────────────────────────────────────┐
│  🔗 Section Title          📁 [Collapse]   │ ← Section Header (clickable)
├─────────────────────────────────────────────┤
│                                             │
│  Section Content Area                       │ ← Section Content
│  - Form controls                            │   (collapsible)
│  - Status indicators                        │
│  - Action buttons                           │
│                                             │
└─────────────────────────────────────────────┘
  ↑                                         ↑
  Background: --surface                     Border: --glass-border
  Padding: 24px                             Radius: 16px
```

#### Collapsible Section
```html
<div class="section" id="sectionId">
    <div class="section-header" onclick="toggleSection('sectionId')">
        <h2>🔗 Section Title</h2>
        <button class="collapse-btn" id="sectionId-btn">📁</button>
    </div>
    <div class="section-content">
        <!-- Section content here -->
    </div>
</div>
```

```css
.section {
    background: var(--surface);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
    transition: all 0.3s ease;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    user-select: none;
}

.section-header h2 {
    margin: 0;
    font-size: 1.3em;
    color: var(--fg);
    display: flex;
    align-items: center;
    gap: 12px;
}

.collapse-btn {
    background: var(--glass-surface);
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 1.2em;
    cursor: pointer;
    transition: all 0.2s ease;
}

.section-content {
    margin-top: 20px;
    overflow: hidden;
    transition: max-height 0.3s ease, opacity 0.3s ease;
}

.section.collapsed .section-content {
    max-height: 0;
    opacity: 0;
    margin-top: 0;
}
```

### 3. Status Indicators

#### Visual Structure
```
┌─────────────────────────────────┐
│  ● Connected to server          │ ← Status pill
└─────────────────────────────────┘
   ↑  ↑
   │  └── Status text
   └── Pulsing indicator (8px circle)

Color Variants:
● Green  (--success) = Connected/Active/Pass
● Red    (--error)   = Disconnected/Fail
● Blue   (--info)    = Processing/Info
● Orange (--warning) = Warning/Partial
```

#### Status Pill
```html
<div class="status connected">
    <span class="status-indicator"></span>
    <span>Connected to server</span>
</div>
```

```css
.status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.9em;
    font-weight: 500;
    transition: all 0.3s ease;
}

.status.connected {
    background: rgba(52, 199, 89, 0.15);
    color: var(--success);
}

.status.disconnected {
    background: rgba(255, 59, 48, 0.15);
    color: var(--error);
}

.status.processing {
    background: rgba(0, 122, 255, 0.15);
    color: var(--info);
}

.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s ease-in-out infinite;
}
```

### 4. Form Controls

#### Visual Structure
```
┌─────────────────────────────────┐
│  Server URL                     │ ← Label (--secondary-fg)
│  ┌───────────────────────────┐  │
│  │ http://example.com        │  │ ← Input field
│  └───────────────────────────┘  │
└─────────────────────────────────┘
     ↑                         ↑
     Background: --input-bg    Border: --input-border
     Padding: 12px 16px        Focus: Blue glow
```

#### Input Field
```html
<div class="control-group">
    <label>Server URL</label>
    <input type="text" placeholder="http://example.com">
</div>
```

```css
.control-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.control-group label {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--secondary-fg);
}

input[type="text"],
input[type="url"],
select {
    background: var(--input-bg);
    border: 1px solid var(--input-border);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 1em;
    color: var(--input-fg);
    transition: all 0.3s ease;
}

input:focus,
select:focus {
    outline: none;
    border-color: var(--input-border-focus);
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}
```

### 5. Cards

#### Visual Structure - Device Card
```
┌─────────────────────────────────────────────────────┐
│ ║  📱 Device 1              ✓ PASS                  │ ← Header
│ ║                                                    │   (4px left border)
│ ║  ┌──────────────────────────────────────────┐     │
│ ║  │ Barcode                                  │     │
│ ║  │ ABC123                                   │     │ ← Device Info Grid
│ ║  ├──────────────────────────────────────────┤     │   (2 columns)
│ ║  │ ROIs Passed                              │     │
│ ║  │ 3/4                                      │     │
│ ║  └──────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
  ↑                                                 ↑
  Left border color:                               Box shadow lifts on hover
  - Green (PASS)                                   Transform: translateY(-2px)
  - Red (FAIL)

Layout Hierarchy:
.device-card
  ├── .device-header
  │   ├── .device-title (📱 Device 1)
  │   └── .device-status.passed (✓ PASS)
  └── .device-info
      └── .device-info-item (x N)
          ├── .device-info-label
          └── .device-info-value
```

#### Device Card
```html
<div class="device-card passed">
    <div class="device-header">
        <div class="device-title">📱 Device 1</div>
        <div class="device-status passed">✓ PASS</div>
    </div>
    <div class="device-info">
        <div class="device-info-item">
            <div class="device-info-label">Barcode</div>
            <div class="device-info-value">ABC123</div>
        </div>
    </div>
</div>
```

```css
.device-card {
    background: var(--surface);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.device-card:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
}

.device-card.passed {
    border-left: 4px solid var(--success);
}

.device-card.failed {
    border-left: 4px solid var(--error);
}
```

### 6. ROI Item

#### Visual Structure - ROI Detail Card
```
┌────────────────────────────────────────────────────────┐
│  ROI 1  [BARCODE]                    ✓ PASS           │ ← ROI Header
├────────────────────────────────────────────────────────┤
│  AI Similarity                                         │
│  88.19% ████████████████████░░░░░░                    │ ← Similarity Bar
│                                                        │   (Color-coded)
│  Barcode Value                                         │
│  ['20003548-0000003-1019720-101']                     │ ← ROI Details
│                                                        │   (Type-specific)
│  Position                                              │
│  [3459, 2959, 4058, 3318]                             │
└────────────────────────────────────────────────────────┘
  ↑                                                    ↑
  Border color matches status                         Padding: 16px
  - Green (PASS)                                       Radius: 10px
  - Red (FAIL)

Type Badge Colors:
[BARCODE]  → Blue (#007AFF)
[OCR]      → Purple (#5856D6)
[COMPARE]  → Orange (#FF9500)
[TEXT]     → Magenta (#AF52DE)

Similarity Bar Colors:
████ High (≥80%)   → Green
████ Medium (60-79%) → Orange
████ Low (<60%)    → Red

Layout Hierarchy:
.roi-item
  ├── .roi-header
  │   ├── .roi-title
  │   │   ├── <span>ROI 1</span>
  │   │   └── .roi-badge.barcode
  │   └── .roi-status-badge.passed
  └── .roi-details
      └── .roi-detail-item (x N)
          ├── .roi-detail-label
          └── .roi-detail-value
              └── .similarity-bar (if similarity)
                  └── .similarity-fill.high
```

#### ROI Detail Card
```html
<div class="roi-item passed">
    <div class="roi-header">
        <div class="roi-title">
            <span>ROI 1</span>
            <span class="roi-badge barcode">BARCODE</span>
        </div>
        <div class="roi-status-badge passed">✓ PASS</div>
    </div>
    <div class="roi-details">
        <div class="roi-detail-item">
            <div class="roi-detail-label">AI Similarity</div>
            <div class="roi-detail-value">
                88.19%
                <div class="similarity-bar">
                    <div class="similarity-fill high" style="width: 88.19%"></div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 7. Modal/Dialog

#### Visual Structure
```
┌──────────────────────────────────────────────────┐
│                 Backdrop Overlay                 │
│   (Semi-transparent, blurred background)         │
│                                                  │
│   ┌────────────────────────────────────┐        │
│   │  Modal Title              ✕ Close │        │ ← Modal Header
│   ├────────────────────────────────────┤        │
│   │                                    │        │
│   │  Modal body content area           │        │ ← Modal Body
│   │  - Forms                           │        │   (scrollable)
│   │  - Information                     │        │
│   │  - Actions                         │        │
│   │                                    │        │
│   └────────────────────────────────────┘        │
│                                                  │
└──────────────────────────────────────────────────┘
     ↑                                  ↑
     Glass effect background            Centered on screen
     Box shadow for elevation           Max-width: 600px
```

```html
<div id="modalId" class="modal" style="display: none;">
    <div class="modal-content">
        <div class="modal-header">
            <h2>Modal Title</h2>
            <button onclick="closeModal()" class="glass-button danger">✕</button>
        </div>
        <div class="modal-body">
            <!-- Modal content -->
        </div>
    </div>
</div>
```

---

## Layout Structure

### Grid System

#### Visual Responsive Behavior
```
Desktop (≥1200px):
┌─────────────────────────────────────────────────────────┐
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Section   │  │  Section   │  │  Section   │        │  3 columns
│  │     1      │  │     2      │  │     3      │        │  (auto-fit)
│  └────────────┘  └────────────┘  └────────────┘        │
└─────────────────────────────────────────────────────────┘
                    max-width: 1400px

Tablet (768px - 1199px):
┌───────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐    │
│  │  Section 1  │  │  Section 2  │    │  2 columns
│  └─────────────┘  └─────────────┘    │  (auto-fit)
│  ┌─────────────┐  ┌─────────────┐    │
│  │  Section 3  │  │  Section 4  │    │
│  └─────────────┘  └─────────────┘    │
└───────────────────────────────────────┘
            gap: 20px

Mobile (≤767px):
┌─────────────────┐
│  ┌───────────┐  │
│  │ Section 1 │  │  1 column
│  └───────────┘  │  (stacked)
│  ┌───────────┐  │
│  │ Section 2 │  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Section 3 │  │
│  └───────────┘  │
└─────────────────┘
   padding: 12px
```

```css
.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.grid {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
}

/* Responsive breakpoints */
@media (max-width: 768px) {
    .grid {
        grid-template-columns: 1fr;
    }
}
```

### Page Structure

```
┌──────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────┐  🌓 Theme      │
│  │  Visual AOI Client                       │  Toggle        │
│  │  Professional Inspection Interface       │                │
│  └──────────────────────────────────────────┘                │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ 🔗 Server Connection│  │ 📷 Camera Controls  │           │
│  │ ● Connected         │  │ [Capture] [Live]    │           │
│  │ http://server:5000  │  │ Status: Ready       │           │
│  └─────────────────────┘  └─────────────────────┘           │  Grid (2 cols)
│  ┌─────────────────────┐  ┌─────────────────────┐           │  min: 400px
│  │ 🏭 Product Config   │  │ 📊 Session Info     │           │  gap: 20px
│  │ Product: ABC123     │  │ ID: sess_001        │           │
│  │ Devices: 4          │  │ Count: 15           │           │
│  └─────────────────────┘  └─────────────────────┘           │
├──────────────────────────────────────────────────────────────┤
│  📊 Inspection Results                          [Export]     │
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐                │
│  │Device │  │ Total │  │ Pass  │  │ Fail  │                │  Stats Grid
│  │   4   │  │  150  │  │  145  │  │   5   │                │  (4 cols)
│  └───────┘  └───────┘  └───────┘  └───────┘                │
│                                                              │
│  Pre-formatted Summary:                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Overall Result: PASS                               │    │  Text Summary
│  │                                                     │    │  (monospace)
│  │ Device 1: PASS                                      │    │
│  │   Barcode: ABC123                                   │    │
│  │   ROIs: 3/3 passed                                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  [🔍 Show Device Details]                                   │
├──────────────────────────────────────────────────────────────┤
│  📱 Device-Separated Inspection Results    (Collapsible)    │
│  ┌────────────────────────────────────────────────────┐    │
│  │ ║ 📱 Device 1                      ✓ PASS          │    │
│  │ ║ Barcode: ABC123  |  ROIs: 3/3                    │    │  Device Card
│  │ ║                                                   │    │  (hover lift)
│  │ ║   ┌─────────────────────────────────────────┐    │    │
│  │ ║   │ ROI 1 [BARCODE]           ✓ PASS        │    │    │
│  │ ║   │ Similarity: 88% ████████████░░░         │    │    │  ROI Items
│  │ ║   └─────────────────────────────────────────┘    │    │  (nested)
│  │ ║   ┌─────────────────────────────────────────┐    │    │
│  │ ║   │ ROI 2 [OCR]               ✓ PASS        │    │    │
│  │ ║   └─────────────────────────────────────────┘    │    │
│  │ └────────────────────────────────────────────────────┘    │
│  │                                                          │
│  │ ┌────────────────────────────────────────────────────┐  │
│  │ ║ 📱 Device 2                      ✗ FAIL          │  │
│  │ ║ Barcode: XYZ789  |  ROIs: 2/3                    │  │
│  │ └────────────────────────────────────────────────────┘  │
│  └──────────────────────────────────────────────────────────┘
├──────────────────────────────────────────────────────────────┤
│  System Info: Camera Ready | Server: 10.100.10.156:5000     │
└──────────────────────────────────────────────────────────────┘

Key Visual Elements:
• ║ = Colored left border (4px) indicating pass/fail
• ● = Pulsing status indicator
• █ = Similarity progress bar (color-coded)
• [BADGE] = Type indicators (blue/purple/orange)
• ✓/✗ = Pass/Fail icons
```

---

## Typography

### Font Stack
```css
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", 
                 Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Monospace for code/data */
code, pre, .code {
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 
                 'Courier New', monospace;
}
```

### Type Scale
```css
h1 { font-size: 2.5em; font-weight: 700; line-height: 1.2; }
h2 { font-size: 1.8em; font-weight: 600; line-height: 1.3; }
h3 { font-size: 1.4em; font-weight: 600; line-height: 1.4; }
h4 { font-size: 1.2em; font-weight: 600; line-height: 1.4; }

body { font-size: 16px; line-height: 1.6; }
small { font-size: 0.875em; }
```

---

## Iconography

### Icon System
Use emoji for simplicity and universal support:

**Categories:**
- 🔗 Connection/Link
- 📷 Camera
- 🏭 Manufacturing/Production
- 📊 Results/Analytics
- 🔍 Inspection/Detail
- ⚙️ Settings
- 📄 Document/Export
- 🔄 Process/Sync
- ✓ Success
- ✗ Fail
- ⚠️ Warning
- ℹ️ Info

**Usage:**
```html
<h2>🔗 Server Connection</h2>
<button>📄 Export Results</button>
<span class="status">✓ PASS</span>
```

---

## Interactive States

### Visual State Transitions
```
Button Interaction Flow:

Default State:
┌─────────────────┐
│  Primary Action │  Opacity: 1.0
└─────────────────┘  Transform: none
        ↓ (mouse over)
        
Hover State:
┌─────────────────┐
│  Primary Action │  Opacity: 1.0
└─────────────────┘  Transform: translateY(-2px)
   ↑↑↑↑↑↑↑↑↑↑↑       Shadow: 0 4px 16px
   Lifted effect
        ↓ (mouse down)
        
Active/Press State:
┌─────────────────┐
│  Primary Action │  Opacity: 1.0
└─────────────────┘  Transform: translateY(0)
   Press down       Shadow: normal
        ↓ (disabled)
        
Disabled State:
┌─────────────────┐
│  Primary Action │  Opacity: 0.5
└─────────────────┘  Cursor: not-allowed
   Grayed out      Transform: none
```

### Button States
```css
/* Default */
.glass-button { opacity: 1; cursor: pointer; }

/* Hover */
.glass-button:hover { 
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 122, 255, 0.3);
}

/* Active/Press */
.glass-button:active { 
    transform: translateY(0);
}

/* Disabled */
.glass-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
}
```

### Focus States
```css
*:focus {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
}

/* Custom focus for inputs */
input:focus, select:focus {
    outline: none;
    border-color: var(--input-border-focus);
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}
```

---

## Animation Guidelines

### Transition Timing
```css
/* Standard transition */
transition: all 0.3s ease;

/* Quick interaction */
transition: all 0.2s ease;

/* Slow reveal */
transition: all 0.5s ease;
```

### Keyframe Animations

#### Pulse
```css
@keyframes pulse {
    0%, 100% { 
        box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1); 
    }
    50% { 
        box-shadow: 0 0 0 6px rgba(0, 122, 255, 0.2); 
    }
}
```

#### Fade In
```css
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
```

#### Slide In Down
```css
@keyframes slideInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Usage Guidelines
- Use animations sparingly
- Keep under 0.5s for UI feedback
- Prefer `ease` or `ease-in-out` easing
- Use `transform` over position changes (better performance)

---

## Responsive Behavior

### Breakpoints
```css
/* Mobile */
@media (max-width: 480px) {
    .container { padding: 12px; }
    .section { padding: 16px; }
}

/* Tablet */
@media (max-width: 768px) {
    .grid { grid-template-columns: 1fr; }
    .device-info { grid-template-columns: 1fr; }
}

/* Desktop */
@media (min-width: 1200px) {
    .container { max-width: 1400px; }
}
```

### Touch Targets
```css
/* Minimum touch target: 44x44px */
button, 
.interactive {
    min-width: 44px;
    min-height: 44px;
}
```

---

## Code Templates

### Section Template
```html
<div class="section" id="newSection">
    <div class="section-header" onclick="toggleSection('newSection')">
        <h2>🔗 Section Title</h2>
        <button class="collapse-btn" id="newSection-btn">📁</button>
    </div>
    <div class="section-content">
        <div class="controls">
            <div class="control-group">
                <label>Label</label>
                <input type="text" placeholder="Placeholder">
            </div>
            <button class="glass-button">Action</button>
        </div>
        <div class="status disconnected">
            <span class="status-indicator"></span>
            <span>Status message</span>
        </div>
    </div>
</div>
```

### Device Card Template
```html
<div class="device-card ${passed ? 'passed' : 'failed'}">
    <div class="device-header">
        <div class="device-title">📱 Device ${deviceId}</div>
        <div class="device-status ${statusClass}">
            ${statusIcon} ${statusText}
        </div>
    </div>
    <div class="device-info">
        <div class="device-info-item">
            <div class="device-info-label">Label</div>
            <div class="device-info-value">Value</div>
        </div>
    </div>
</div>
```

### ROI Item Template
```html
<div class="roi-item ${statusClass}">
    <div class="roi-header">
        <div class="roi-title">
            <span>ROI ${roi.roi_id}</span>
            <span class="roi-badge ${roi.roi_type_name}">
                ${roi.roi_type_name}
            </span>
        </div>
        <div class="roi-status-badge ${statusClass}">
            ${statusIcon} ${statusText}
        </div>
    </div>
    <div class="roi-details">
        <div class="roi-detail-item">
            <div class="roi-detail-label">Label</div>
            <div class="roi-detail-value">Value</div>
        </div>
    </div>
</div>
```

---

## Implementation Checklist

### When Adding New Components

- [ ] Use CSS custom properties (variables) for colors
- [ ] Apply glass button styles for actions
- [ ] Add hover/focus states
- [ ] Include loading/disabled states
- [ ] Add smooth transitions (0.2s-0.5s)
- [ ] Test in both light and dark themes
- [ ] Verify on mobile/tablet/desktop
- [ ] Use semantic HTML
- [ ] Add ARIA labels where needed
- [ ] Test keyboard navigation
- [ ] Ensure 44px minimum touch targets
- [ ] Add status indicators where applicable
- [ ] Include appropriate icons
- [ ] Test with actual data
- [ ] Document in this guide

### Accessibility Requirements

- [ ] Color contrast ratio ≥ 4.5:1 for text
- [ ] Status conveyed through icons AND color
- [ ] Keyboard navigation support
- [ ] Focus indicators visible
- [ ] ARIA labels on interactive elements
- [ ] Alt text for images
- [ ] Semantic HTML structure
- [ ] Screen reader testing

---

## File Organization

```
visual-aoi-client/
├── static/
│   ├── professional.css      # Main stylesheet
│   └── [other assets]
├── templates/
│   └── professional_index.html   # Main UI
├── docs/
│   ├── UI_DESIGN_SCAFFOLD.md     # This file
│   └── [other docs]
└── [other files]
```

---

## Best Practices

### DO ✅
- Use CSS variables for all colors
- Apply transitions to interactive elements
- Include hover/focus states
- Use semantic HTML
- Test in both themes
- Keep components modular
- Follow established patterns
- Document new components

### DON'T ❌
- Use hardcoded colors (#007AFF)
- Forget disabled states
- Ignore mobile viewport
- Over-animate (keep it subtle)
- Create inconsistent spacing
- Skip accessibility testing
- Reinvent existing components

---

## Quick Reference

### Common Classes
```css
.glass-button           /* Primary button */
.glass-button.secondary /* Secondary button */
.glass-button.success   /* Success button */
.glass-button.danger    /* Danger button */

.section                /* Collapsible section */
.section-header         /* Section header */
.section-content        /* Section body */

.status                 /* Status indicator */
.status.connected       /* Connected status */
.status.disconnected    /* Disconnected status */

.device-card            /* Device container */
.device-card.passed     /* Passed device */
.device-card.failed     /* Failed device */

.roi-item               /* ROI container */
.roi-badge              /* Type badge */
.similarity-bar         /* Progress bar */
```

### Common Patterns
```javascript
// Toggle section
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const content = section.querySelector('.section-content');
    const btn = document.getElementById(sectionId + '-btn');
    
    if (appState.collapsedSections.has(sectionId)) {
        // Expand
        content.style.maxHeight = content.scrollHeight + 'px';
        section.classList.remove('collapsed');
        btn.textContent = '📁';
        appState.collapsedSections.delete(sectionId);
    } else {
        // Collapse
        content.style.maxHeight = '0';
        section.classList.add('collapsed');
        btn.textContent = '📂';
        appState.collapsedSections.add(sectionId);
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Implementation
}

// Update status
function updateStatus(elementId, state, message) {
    const el = document.getElementById(elementId);
    el.className = `status ${state}`;
    el.querySelector('span:last-child').textContent = message;
}
```

---

## Maintenance

### Version History
- **v2.0** (Oct 3, 2025): Added device details UI, removed JSON toggle
- **v1.5** (Previous): Device-separated results
- **v1.0** (Initial): Base professional UI

### Review Schedule
- **Quarterly**: Review and update color system
- **Bi-annual**: Audit component usage
- **Annual**: Major design system refresh

### Contributing
When adding new components:
1. Follow this scaffold
2. Test thoroughly
3. Document in this file
4. Update version history

---

## Related Documentation
- `static/professional.css` - Complete stylesheet
- `templates/professional_index.html` - Main implementation
- `docs/DEVICE_SEPARATED_UI_IMPLEMENTATION.md` - Device UI details
- `.github/copilot-instructions.md` - Development guidelines

---

**Last Updated:** October 3, 2025  
**Maintained By:** Development Team  
**Status:** Active Reference Document
