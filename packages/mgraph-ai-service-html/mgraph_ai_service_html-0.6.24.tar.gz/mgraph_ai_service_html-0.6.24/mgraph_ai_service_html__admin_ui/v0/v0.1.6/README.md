# HTML Service Admin UI - v0.1.6 (Component Architecture)

**Version**: v0.1.6  
**Status**: ✅ Complete  
**Type**: Major Refactoring (Component-based architecture)

---

## Overview

This is the **component architecture refactoring** of the HTML Service Admin UI. It transforms the monolithic playground into a **modular, event-driven system** built with **Web Components** that communicate through a central orchestrator.

### What's Included

✅ **Playground Page** (`playground.html`)  
   - 3-column grid layout for transformation workflow
   - Component-based architecture with orchestrator
   - Event-driven communication between components
   - Real-time HTML transformation pipeline

✅ **Playground Controller** (`components/playground-controller/`)  
   - Central orchestrator for state and API calls
   - Event listener hub for all component communication
   - No direct DOM manipulation
   - Handles: parse, rebuild, copy, download actions

✅ **Column Components** (`components/column-*/`)  
   - **column-original**: Original HTML input with edit/view modes
   - **column-middle**: Layout & content objects (Dict + Hashes)
   - **column-created**: Reconstructed HTML output
   - Each manages its own DOM and state independently

✅ **Shared Components** (`components/columns-shared/`)  
   - **column-header**: Reusable header with Shadow DOM
   - Supports mode tabs, icons, title, and action slots
   - Consistent styling across all columns

✅ **Mode Components** (View and Edit modes)  
   - **html-view-mode**: Syntax-highlighted HTML display
   - **html-edit-mode**: Textarea editor for HTML
   - **json-view-mode**: Formatted JSON with syntax highlighting
   - **json-edit-mode**: JSON textarea with validation
   - **sample-selector**: Dropdown for loading sample files

✅ **UI Components** (`components/mode-tabs/`, `components/debug-panel/`)  
   - **mode-tabs**: View/Edit mode switcher
   - **debug-panel**: Quick testing controls for development

✅ **Component Utilities** (`utils/ComponentUtils.js`)  
   - Template loading from external HTML files
   - CSS loading (global and Shadow DOM)
   - Event emission and handling helpers
   - DOM query shortcuts ($, $$)
   - Utility functions (debounce, toggle, etc.)

✅ **Playground Grid Layout** (`css/playground.css`)  
   - 3-column responsive grid system
   - Column styling and spacing
   - Status message styles
   - Button and control styles

✅ **Legacy Dependencies** (from v0.1.1)  
   - Navigation component (top-nav)
   - Common styles (base theme)
   - Dashboard functionality

---

## Usage

### Access the Playground

Navigate to: `/html-service/v0/v0.1.6/playground.html`

The playground will load with:
- Original HTML input column (left)
- Layout & Content Objects column (middle)
- Created HTML output column (right)
- Debug panel (bottom-right corner)

### Transformation Workflow

1. **Load HTML**:
   - Use sample selector dropdown to load pre-defined samples
   - Switch to Edit mode to paste or type HTML
   - Switch to View mode to see syntax-highlighted display

2. **Parse HTML**:
   - Click **"▶ Parse"** button in middle column
   - Generates HTML Dict (structure/layout)
   - Generates Text Hashes (content)
   - Both displayed in middle column

3. **Rebuild HTML**:
   - Click **"🔄 Rebuild"** button in right column
   - Reconstructs HTML from Dict + Hashes
   - Displays result in right column

4. **Copy or Download**:
   - Click **"📋 Copy"** to copy HTML to clipboard
   - Click **"⬇ Download"** to save as .html file

### Debug Panel

Quick testing controls for development:
- **📝 Load Micro Sample**: Minimal HTML for testing
- **📄 Load Simple Sample**: Basic structured HTML
- **▶️ Parse HTML**: Trigger parse action
- **🔄 Rebuild HTML**: Trigger rebuild action
- **⚡ Full Flow**: Load → Parse → Rebuild in sequence

---

## Architecture

### Component-Based Design

This version uses **Web Components** with a clear separation of concerns:

**Orchestrator Pattern**:
- `playground-controller`: Central coordinator
- No direct DOM manipulation in controller
- Event-driven communication only
- State management centralized

**Column Components**:
- Self-contained and independent
- Manage their own DOM and state
- Emit events for actions (parse, rebuild, copy, etc.)
- Listen for data updates from controller

**Mode Components**:
- Swappable view/edit modes
- Each mode is a separate component
- Clean separation between display and editing

### Zero External Dependencies

This version uses **only native web platform features**:
- ✅ ES6 Modules
- ✅ Web Components API (Custom Elements)
- ✅ Shadow DOM (for column-header)
- ✅ Template loading via fetch
- ✅ CSS3 with custom properties
- ✅ Fetch API for HTTP requests
- ❌ No React, Vue, Angular, jQuery, or any frameworks
- ❌ No build tools or bundlers

### File Organization

```
v0.1.6/
├── playground.html                        # Main playground page
├── README.md                              # This file
├── css/
│   └── playground.css                     # Grid layout and styles
├── components/
│   ├── playground-controller/
│   │   └── playground-controller.js       # Orchestrator component
│   ├── column-original/
│   │   ├── column-original.html           # Template
│   │   ├── column-original.js             # Component logic
│   │   ├── column-original.css            # Column styles
│   │   ├── sample-selector/               # Sample dropdown
│   │   ├── html-edit-mode/                # HTML editor
│   │   └── html-view-mode/                # HTML viewer
│   ├── column-middle/
│   │   ├── column-middle.html             # Template
│   │   ├── column-middle.js               # Component logic
│   │   ├── column-middle.css              # Column styles
│   │   ├── json-view-mode/                # JSON viewer (x2)
│   │   └── json-edit-mode/                # JSON editor (x2)
│   ├── column-created/
│   │   ├── column-created.html            # Template
│   │   ├── column-created.js              # Component logic
│   │   └── column-created.css             # Column styles
│   ├── columns-shared/
│   │   └── column-header/                 # Shared header component
│   │       ├── column-header.js           # Shadow DOM component
│   │       └── column-header.css          # Shadow DOM styles
│   ├── mode-tabs/
│   │   ├── mode-tabs.js                   # Mode switcher
│   │   └── mode-tabs.css                  # Tab styles
│   └── debug-panel/
│       ├── debug-panel.js                 # Debug controls
│       └── debug-panel.css                # Panel styles
└── utils/
    └── ComponentUtils.js                  # Component helper utilities
```

### Key Components

**Playground Controller** (`playground-controller.js`):
- Invisible orchestrator element: `<playground-controller>`
- Listens to all component events
- Manages global state (originalHtml, currentDict, currentHashes, etc.)
- Makes API calls to transformation endpoints
- Dispatches results back to components
- Methods: `handleParse()`, `handleRebuild()`, `handleCopy()`, `handleDownload()`

**Column Original** (`column-original.js`):
- Manages original HTML input
- Contains: sample-selector, html-edit-mode, html-view-mode
- Emits: `html-changed` event when HTML is modified
- Supports view/edit mode switching

**Column Middle** (`column-middle.js`):
- Displays HTML Dict and Text Hashes
- Contains: json-view-mode (x2), json-edit-mode (x2)
- Emits: `parse-requested`, `dict-changed`, `hashes-changed` events
- Dual display: structure (Dict) and content (Hashes)

**Column Created** (`column-created.js`):
- Displays reconstructed HTML output
- Contains: html-view-mode for display
- Emits: `rebuild-requested`, `copy-requested`, `download-requested` events
- Copy and download actions

**Column Header** (`column-header.js`):
- Reusable header with Shadow DOM
- Attributes: title, icon, modes, active-mode, column-id
- Contains mode-tabs component
- Slots for custom action buttons

**Component Utils** (`ComponentUtils.js`):
- `loadTemplate()`: Fetch and inject HTML templates
- `loadStyles()`: Load CSS into document head
- `loadShadowStyles()`: Load CSS into Shadow DOM
- `emitEvent()`: Dispatch custom events with detail
- `$()` / `$$()`: Query selector shortcuts
- `toggle()`, `debounce()`: Common utilities

---

## Component Communication

### Event-Driven Architecture

All components communicate through custom events:

**Events Emitted**:
```javascript
// From column-original
'html-changed' → { html: string }

// From column-middle
'parse-requested' → {}
'dict-changed' → { dict: object }
'hashes-changed' → { hashes: object }

// From column-created
'rebuild-requested' → {}
'copy-requested' → {}
'download-requested' → {}

// From debug-panel
'debug-action' → { action: string }

// From mode-tabs
'mode-selected' → { mode: string, columnId: string }
```

**Event Flow Example**:
```
User clicks "Parse" button
  ↓
column-middle emits 'parse-requested'
  ↓
playground-controller hears event
  ↓
controller makes API call: POST /html/to/dict/hashes
  ↓
controller receives { html_dict, hash_mapping }
  ↓
controller calls columnMiddle.setData(dict, hashes)
  ↓
column-middle updates its child components
  ↓
json-view-mode components display the data
```

### Component Methods

**Public API Methods**:
```javascript
// column-original
columnOriginal.loadSample('micro' | 'simple' | 'complex')
columnOriginal.getData() → string

// column-middle
columnMiddle.setData(dict, hashes)
columnMiddle.getData() → { dict, hashes }

// column-created
columnCreated.setHtml(html)
columnCreated.getData() → string

// json-view-mode
jsonViewMode.setData(jsonObject)
jsonViewMode.getData() → object

// json-edit-mode
jsonEditMode.setData(jsonObject)
jsonEditMode.getData() → object
```

---

## API Integration

### Endpoints Used

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

### Error Handling

All API calls include error handling:
- HTTP status code validation
- Try-catch blocks around fetch calls
- User-friendly error messages via status display
- Console logging for debugging

---

## Styling System

### CSS Architecture

**Global Styles** (from v0.1.1):
- `common.css`: Base theme, gradients, typography
- Color variables and spacing system

**Component Styles**:
- Each component has its own CSS file
- Scoped to component via class names
- No style conflicts between components

**Shadow DOM Styles** (column-header):
- Isolated styles for header component
- Prevents global style leakage
- `::slotted()` selectors for Light DOM content

### Grid Layout

**3-Column Grid**:
```css
.playground-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1.5rem;
    height: calc(100vh - 300px);
}
```

**Responsive Design**:
- Collapses to single column on smaller screens
- Maintains usability on mobile devices

---

## Sample Files

### Available Samples

**Micro Sample** (`micro`):
- Minimal HTML for quick testing
- ~15 text nodes, depth 5
- Good for debugging single transformations

**Simple Sample** (`simple`):
- Basic structured HTML document
- ~30 text nodes, depth 8
- Common use case testing

**Complex Sample** (`complex`):
- Deeply nested HTML structure
- 100+ text nodes, depth 15+
- Stress testing and edge cases

Samples are defined in: `v0.1.5/data/samples.js`

---

## Benefits Over Previous Versions

### Compared to v0.1.5

**Modularity**:
- ✅ Self-contained components vs. monolithic code
- ✅ Each component has single responsibility
- ✅ Easy to add new features by adding components

**Maintainability**:
- ✅ Clear separation of concerns
- ✅ Components can be tested independently
- ✅ Template HTML separated from JavaScript logic

**Scalability**:
- ✅ Easy to add new transformation modes
- ✅ Easy to add new column types
- ✅ Event system scales to any number of components

**Reusability**:
- ✅ column-header used across all columns
- ✅ json-view-mode and json-edit-mode reused
- ✅ ComponentUtils library for common tasks

**Developer Experience**:
- ✅ External HTML templates (easier editing)
- ✅ Component registration is automatic
- ✅ Event names are self-documenting

---

## Development Notes

### Creating New Components

1. Create component folder with files:
   - `component-name.js` (logic)
   - `component-name.html` (template)
   - `component-name.css` (styles)

2. Use ComponentUtils for common tasks:
   ```javascript
   import { ComponentUtils } from '../path/to/ComponentUtils.js';
   
   class MyComponent extends HTMLElement {
       async connectedCallback() {
           ComponentUtils.loadStyles('my-styles', './my-component.css');
           await ComponentUtils.loadTemplate(this, './my-component.html');
           this.attachListeners();
       }
   }
   ```

3. Register component:
   ```javascript
   customElements.define('my-component', MyComponent);
   ```

4. Add to playground.html:
   ```html
   <script type="module" src="./components/my-component/my-component.js"></script>
   ```

### Adding New Events

1. Emit from component:
   ```javascript
   ComponentUtils.emitEvent(this, 'my-event', { data: value });
   ```

2. Listen in controller:
   ```javascript
   document.addEventListener('my-event', (e) => {
       console.log('Received:', e.detail.data);
   });
   ```

### Debugging

- Use Debug Panel for quick testing
- Check browser console for component lifecycle logs
- All components log their registration
- Event emissions are logged with detail

---


## Version History

- **v0.1.0**: Foundation with dashboard
- **v0.1.1**: Navigation and common styles
- **v0.1.2**: API client service
- **v0.1.3**: Transformation selector
- **v0.1.4**: Output viewer refactoring
- **v0.1.5**: Added micro sample
- **v0.1.6**: **Component architecture refactoring** ⭐