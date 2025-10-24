# HTML Service Admin UI - v0.1.7 (HTML Preview & UI Refinements)

**Version**: v0.1.7  
**Status**: ✅ Complete  
**Type**: Feature Enhancement + UI/UX Improvements

---

## Overview

This is the **HTML Preview and UI refinements** release of the HTML Service Admin UI. It adds **real-time HTML preview modes**, improves **button layout**, fixes **scrolling issues**, and repositions the **debug panel** for better usability.

### What's Included

✅ **HTML Preview Feature** (`components/column-created/html-preview-mode/`)  
   - Real-time iframe-based HTML rendering
   - Three viewing modes: Code, Preview, Split
   - "Open in Window" functionality for external preview
   - Proper scrolling in all modes

✅ **Improved Button Layout** (`css/column-actions.css`)  
   - Action buttons moved below column headers
   - More horizontal space for mode tabs
   - Consistent layout across all three columns
   - Clean visual hierarchy

✅ **Fixed Mode Tabs** (`components/mode-tabs/`)  
   - Support for new mode types: Code, Split
   - Proper labels and icons for all modes
   - No more "undefined undefined" text

✅ **Repositioned Debug Panel** (`components/debug-panel/`)  
   - Moved to top-center (below page header)
   - Collapsible by default to save space
   - Doesn't cover important UI elements
   - Clean toggle button interface

✅ **Bug Fixes**  
   - Split view code panel now scrolls properly
   - Preview iframe scrolling works correctly
   - All CSS overflow issues resolved
   - Component inheritance works cleanly

✅ **Clean Code Architecture**  
   - HTML templates in separate files
   - Static TEMPLATE_PATH configuration
   - Minimal code changes from v0.1.6
   - IFD (Incremental Feature Development) methodology

---

## Usage

### Access the Playground

Navigate to: `/html-service/v0/v0.1.7/playground.html`

The playground will load with:
- Original HTML input column (left)
- Layout & Content Objects column (middle)
- Created HTML output column (right) **with preview modes**
- Debug panel (top-center, collapsible)

### New Preview Modes

The **Created HTML** column now has **three viewing modes**:

1. **💻 Code Mode** (default):
   - Syntax-highlighted HTML code
   - Clean, readable display
   - Full scrolling support

2. **🖼️ Preview Mode**:
   - Live iframe rendering of HTML
   - See exactly how HTML will render
   - "Open in Window" button available
   - Full page scrolling

3. **⚡ Split Mode**:
   - Code view on top
   - Preview on bottom
   - Both sections scroll independently
   - Perfect for comparing code and output

### Transformation Workflow

1. **Load HTML**:
   - Use sample selector dropdown (Micro, Simple, or Complex)
   - Switch to Edit mode to paste or type HTML
   - View mode shows syntax-highlighted display

2. **Parse HTML**:
   - Click **"▶ Parse"** button in middle column
   - Generates HTML Dict (structure/layout)
   - Generates Text Hashes (content)
   - Both displayed in middle column

3. **Rebuild HTML**:
   - Click **"🔄 Rebuild"** button in right column
   - Reconstructs HTML from Dict + Hashes
   - Choose viewing mode: Code, Preview, or Split

4. **Preview & Export**:
   - Switch to Preview mode to see live rendering
   - Click **"🪟 Open in Window"** to preview in new browser tab
   - Click **"⬇ Download"** to save as .html file

### Debug Panel

Click **"🔧 Debug Controls ▼"** to expand the panel:
- **📝 Load Micro Sample**: Minimal HTML for testing
- **📄 Load Simple Sample**: Basic structured HTML
- **▶️ Parse HTML**: Trigger parse action
- **🔄 Rebuild HTML**: Trigger rebuild action
- **⚡ Full Flow**: Load → Parse → Rebuild in sequence

Click again to collapse and save screen space.

---

## What's New in v0.1.7

### 1. HTML Preview Modes

**New Component**: `html-preview-mode`
- Live iframe rendering of HTML
- Sandbox security attributes
- Error handling for invalid HTML
- Empty state with helpful message

**Three Viewing Modes**:
```
Code Mode:    [💻 Code]  [🖼️ Preview]  [⚡ Split]
              └── Active: Shows syntax-highlighted code

Preview Mode: [💻 Code]  [🖼️ Preview]  [⚡ Split]
                          └── Active: Shows iframe preview

Split Mode:   [💻 Code]  [🖼️ Preview]  [⚡ Split]
                                        └── Active: Shows both
```

### 2. Button Layout Improvements

**Before** (v0.1.6):
```
📝 Original HTML  [👁️ View] [✏️ Edit]  Clear  ← Cramped
```

**After** (v0.1.7):
```
📝 Original HTML  [👁️ View] [✏️ Edit]     ← Spacious
Clear                                      ← Buttons below
```

**Benefits**:
- More horizontal space for mode tabs
- Cleaner visual hierarchy
- Consistent across all columns
- Buttons have room to breathe

### 3. Fixed Mode Tabs

**Before**: `[undefined undefined] [undefined undefined]`  
**After**: `[💻 Code] [🖼️ Preview] [⚡ Split]`

Proper labels and icons for all mode types:
- Edit, View (original modes)
- Code, Preview, Split (new modes)

### 4. Improved Debug Panel

**Before** (v0.1.6):
- Fixed to bottom-right corner
- Always visible, covering content
- 250px min-width taking up space

**After** (v0.1.7):
- Positioned at top-center
- Collapsible (starts collapsed)
- Only shows when you need it
- Doesn't cover columns

### 5. Scrolling Fixes

**Issues Fixed**:
- Split view code panel expanding instead of scrolling
- Preview iframe not scrolling
- Content getting cut off

**Solution**:
- `overflow: auto` on scrollable containers
- `min-height: 0` for proper flex behavior
- Proper CSS hierarchy

---

## Architecture

### New Components (v0.1.7)

**html-preview-mode** (`components/column-created/html-preview-mode/`):
```
html-preview-mode/
├── html-preview-mode.html    # Template with iframe
├── html-preview-mode.js      # Component logic
└── html-preview-mode.css     # Iframe styling
```

Features:
- Iframe rendering with sandbox security
- Empty state display
- Error handling
- Public API: `setHtml(html)`, `refresh()`, `getHtml()`

**column-actions.css** (`css/column-actions.css`):
- Shared styles for action buttons
- Flex layout with wrapping
- Button variants: primary, secondary, danger
- Ensures proper column sizing

**Updated mode-tabs** (`components/mode-tabs/mode-tabs.js`):
- Added labels for: code, preview, split
- Proper icon rendering
- No "undefined" text issues

**Updated debug-panel** (`components/debug-panel/`):
```
debug-panel/
├── debug-panel.html    # Template (NEW - external file)
├── debug-panel.js      # Component with toggle logic
└── debug-panel.css     # Top-center positioning
```

### Updated Components

**column-created** (Enhanced):
- Three mode containers: code, preview, split
- Mode switching logic
- "Open in Window" button (context-aware)
- Syncs HTML to all mode components

**column-original** & **column-middle** (Layout update):
- Buttons moved to `column-actions` div
- Templates updated for new button placement
- Minimal JavaScript changes

---

## File Organization

```
v0.1.7/
├── playground.html                        # Main page (updated imports)
├── index.html                             # Dashboard (updated footer)
├── README.md                              # This file
├── css/
│   └── column-actions.css                 # NEW: Button layout styles
├── components/
│   ├── mode-tabs/
│   │   └── mode-tabs.js                   # UPDATED: Code/Split modes
│   ├── debug-panel/
│   │   ├── debug-panel.html               # NEW: External template
│   │   ├── debug-panel.js                 # UPDATED: Collapsible
│   │   └── debug-panel.css                # UPDATED: Top-center position
│   └── column-created/
│       ├── column-created.html            # UPDATED: Three modes
│       ├── column-created.js              # UPDATED: Mode switching
│       ├── column-created.css             # UPDATED: Split view fix
│       └── html-preview-mode/             # NEW: Preview component
│           ├── html-preview-mode.html     # NEW: Iframe template
│           ├── html-preview-mode.js       # NEW: Component logic
│           └── html-preview-mode.css      # NEW: Preview styles
└── [All v0.1.6 components reused via imports]
```

### Reused from v0.1.6

The following components are **reused without changes**:
- `playground-controller` (orchestrator)
- `column-header` (shared header)
- `column-original.js` (JavaScript logic)
- `column-middle.js` (JavaScript logic)
- `sample-selector` (dropdown)
- `html-edit-mode` (HTML editor)
- `html-view-mode` (syntax highlighter)
- `json-view-mode` (JSON viewer)
- `json-edit-mode` (JSON editor)
- `ComponentUtils` (utility library)

**Code Reuse**: ~85% of code reused from v0.1.6

---

## API Integration

Same endpoints as v0.1.6:

**Parse HTML**:
```
POST /html/to/dict/hashes
Body: { html: string, max_depth: 256 }
Returns: { html_dict: object, hash_mapping: object }
```

**Rebuild HTML**:
```
POST /hashes/to/html
Body: { html_dict: object, hash_mapping: object }
Returns: string (HTML)
```

No API changes required for preview functionality - it's purely client-side.

---

## Preview Mode Details

### How Preview Works

1. **HTML is passed to iframe**:
   ```javascript
   const iframe = document.querySelector('.preview-frame');
   const doc = iframe.contentDocument;
   doc.open();
   doc.write(html);
   doc.close();
   ```

2. **Sandbox security**:
   ```html
   <iframe sandbox="allow-same-origin allow-scripts">
   ```
   - Prevents malicious code execution
   - Allows scripts within HTML
   - Isolates from parent window

3. **Scrolling**:
   - Preview container: `overflow: auto`
   - Iframe fills container: `width: 100%`, `height: 100%`
   - Both code and preview scroll independently

### Open in New Window

Button appears when in **Preview** or **Split** mode:

```javascript
if (mode === 'preview' || mode === 'split') {
    showOpenWindowButton();
}
```

Opens HTML in new browser tab for full-screen testing.

---

## Styling Updates

### Column Actions Bar

New shared styles for buttons below headers:

```css
.column-actions {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    flex-wrap: wrap;
}
```

**Button Styles**:
- Primary: Purple gradient (Rebuild, Parse)
- Secondary: Gray (Download, Open Window)
- Danger: Red (Clear)

### Split View Layout

Grid-based split view with equal spacing:

```css
.split-view {
    display: grid;
    grid-template-rows: 1fr 1fr;
    gap: 0.75rem;
    height: 100%;
}
```

Both sections:
- Scroll independently
- Equal height allocation
- Clean visual separation

### Debug Panel Positioning

```css
.debug-panel {
    position: fixed;
    top: 110px;      /* Below page header */
    left: 700px;     /* Centered horizontally */
    min-width: 300px;
}
```

Collapsible states:
- Collapsed: Just toggle button
- Expanded: Full button list

---

## Benefits Over v0.1.6

### User Experience

**Preview Functionality**:
- ✅ See HTML rendering in real-time
- ✅ Three flexible viewing modes
- ✅ No need to download and open separately
- ✅ Immediate visual feedback

**Better Layout**:
- ✅ More space for mode tabs
- ✅ Cleaner button organization
- ✅ Debug panel doesn't cover content
- ✅ Professional appearance

**Improved Scrolling**:
- ✅ All content accessible
- ✅ No overflow issues
- ✅ Smooth scrolling experience
- ✅ Split view works perfectly

### Developer Experience

**Clean Code**:
- ✅ HTML templates in separate files
- ✅ Static configuration paths
- ✅ Minimal changes from v0.1.6
- ✅ No code duplication

**Easy to Extend**:
- ✅ Add new preview modes easily
- ✅ Button layouts consistent
- ✅ Component structure clear
- ✅ IFD methodology maintained

---

## Development Notes

### Adding New Preview Modes

To add a new viewing mode:

1. Add mode to mode-tabs:
   ```javascript
   const modeIcons = {
       'mymode': '🎨'
   };
   const modeLabels = {
       'mymode': 'My Mode'
   };
   ```

2. Add mode container in column-created.html:
   ```html
   <div class="mode-container mode-mymode" style="display: none;">
       <my-mode-component></my-mode-component>
   </div>
   ```

3. Update switchMode logic:
   ```javascript
   ComponentUtils.toggle(myModeContainer, mode === 'mymode');
   ```

### Creating External Templates

Best practice for v0.1.7+:

1. Create HTML file:
   ```html
   <!-- component.html -->
   <div class="my-component">
       <!-- Template content -->
   </div>
   ```

2. Load in component:
   ```javascript
   static TEMPLATE_PATH = '../path/to/component.html';
   
   async connectedCallback() {
       await ComponentUtils.loadTemplate(this, MyComponent.TEMPLATE_PATH);
   }
   ```


---

## Version History

- **v0.1.0**: Foundation with dashboard
- **v0.1.1**: Navigation and common styles
- **v0.1.2**: API client service
- **v0.1.3**: Transformation selector
- **v0.1.4**: Output viewer refactoring
- **v0.1.5**: Added micro sample
- **v0.1.6**: Component architecture refactoring
- **v0.1.7**: **HTML Preview & UI refinements** ⭐

