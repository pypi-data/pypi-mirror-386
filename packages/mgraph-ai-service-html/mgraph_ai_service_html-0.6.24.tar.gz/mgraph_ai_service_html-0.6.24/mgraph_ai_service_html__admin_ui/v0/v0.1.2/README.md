# HTML Service Admin UI - v0.1.2 (ES6 Modules & Refactoring)

**Version**: v0.1.2  
**Status**: ✅ Complete & Production Ready  
**Type**: Minor Version (Architecture Upgrade)  
**Focus**: ES6 modules, code quality, separation of concerns

---

## 🎯 Overview

v0.1.2 represents a **major architectural upgrade** that modernizes the codebase by:
- Converting to ES6 modules (eliminating `window.*` globals)
- Creating centralized endpoint configuration
- Simplifying API client and components
- Fixing bugs and improving code quality

This version maintains **100% backward compatibility** while establishing a modern, maintainable foundation for future development.

---

## ✨ What's New

### 1. ES6 Module Architecture ✅
- **No more global pollution**: Eliminated all `window.*` globals
- **Explicit dependencies**: Clear `import`/`export` statements
- **Better tooling**: IDE autocomplete, refactoring support
- **Modern JavaScript**: Following current best practices

### 2. Centralized Configuration ✅
- **Single source of truth**: `Endpoints__Config.js` for all 9 API endpoints
- **Rich metadata**: Routes, types, parameters, descriptions
- **Utility functions**: Query helpers for endpoint data
- **Add endpoints in ONE place**: Everything updates automatically

### 3. Simplified Architecture ✅
- **API Client**: -43% lines of code (105 → 60 lines)
- **TransformationSelector**: -40% lines (175 → 105 lines)
- **Playground Orchestrator**: Cleaner, more maintainable
- **Zero duplication**: DRY principles throughout

### 4. Bug Fixes ✅
- Fixed timing issue with initial HTML loading
- Fixed duplicate dropdown options
- Fixed path inconsistencies
- Added better error messages with context

---

## 📁 File Structure

### v0.1.2 Files (NEW/CHANGED)

```
v0.1.2/
├── index.html                                      # Dashboard (unchanged from v0.1.1)
├── playground.html                                 # Playground with module script
├── README.md                                       # This file
│
├── js/
│   ├── config/
│   │   └── Endpoints__Config.js                   # ES6 module - endpoint config
│   │
│   ├── services/
│   │   └── API__Client.js                         # ES6 module - HTTP client
│   │
│   └── playground.js                               # ES6 module - orchestrator
│
└── components/
    └── transformation-selector/
        └── Transformation__Selector.js             # ES6 module - selector component
```

### Referenced from v0.1.1 (UNCHANGED)

```
../v0.1.1/
├── css/
│   ├── common.css                                  # Shared styles
│   ├── dashboard.css                               # Dashboard styles
│   └── playground.css                              # Playground styles
│
├── components/
│   ├── top-nav/                                    # Navigation component
│   ├── html-input/                                 # Input panel component
│   └── output-viewer/                              # Output display component
│
├── js/
│   ├── services/api-client.js                     # Old version (for dashboard)
│   └── dashboard.js                                # Dashboard logic
│
└── samples/                                        # Sample HTML files
```

---

## 🏗️ Architecture

### ES6 Module Flow

```
playground.html
    │
    └── <script type="module" src="./js/playground.js">
            │
            ├── import { apiClient } from './services/API__Client.js'
            │       │
            │       └── import { Endpoints__Config, Endpoints__Utils } from '../config/Endpoints__Config.js'
            │
            └── import './components/transformation-selector/Transformation__Selector.js'
                    │
                    └── import { Endpoints__Utils } from '../../js/config/Endpoints__Config.js'
```

**Key Benefits**:
- ✅ Explicit dependency tree
- ✅ No global namespace pollution
- ✅ Better IDE support
- ✅ Tree shaking possible
- ✅ Modern JavaScript patterns

---

## 🚀 Usage

### For End Users

1. **Navigate to Playground**:
   ```
   http://your-server/html-service/v0/v0.1.2/playground.html
   ```

2. **Select Transformation**:
   - Dropdown auto-populated from config
   - Choose from 9 transformations
   - See description for selected endpoint

3. **Transform**:
   - Default sample loads automatically
   - Click "Transform" button
   - View results instantly

### For Developers

#### Adding a New Endpoint

**Only edit ONE file**: `js/config/Endpoints__Config.js`

```javascript
export const Endpoints__Config = {
    // ... existing endpoints
    
    'html-to-markdown': {
        id              : 'html-to-markdown'                                    ,
        display_name    : 'HTML → Markdown'                                     ,
        route           : '/html/to/markdown'                                   ,
        method          : 'POST'                                                ,
        description     : 'Convert HTML to Markdown format'                     ,
        category        : 'html'                                                ,
        input_type      : 'html'                                                ,
        output_type     : 'text'                                                ,
        requires_max_depth: false                                               ,
        parameters      : {
            html       : { required: true , type: 'string' }                    ,
            max_depth  : { required: false, type: 'integer', default: 256 }
        }
    }
};
```

**That's it!** The dropdown, API calls, and error handling all update automatically.

#### Using the API Client

```javascript
// Import the client
import { apiClient } from './services/API__Client.js';

// Method 1: Call by endpoint ID (recommended)
const result = await apiClient.call_by_id(
    'html-to-dict',
    '<p>Hello</p>',
    { max_depth: 256 }
);

// Method 2: Build payload manually (advanced)
const payload = apiClient.build_payload('html-to-dict', html_string);
const result = await apiClient.call_endpoint('/html/to/dict', payload);
```

#### Querying Endpoint Config

```javascript
// Import utilities
import { Endpoints__Utils } from './config/Endpoints__Config.js';

// Get specific endpoint
const endpoint = Endpoints__Utils.get_endpoint('html-to-dict');

// Get all HTML endpoints
const html_endpoints = Endpoints__Utils.get_by_category('html');

// Get all endpoint IDs
const all_ids = Endpoints__Utils.get_all_ids();

// Get endpoints grouped by category
const grouped = Endpoints__Utils.get_grouped_by_category();
```

---

## 🔧 Technical Details

### ES6 Module Exports

**Endpoints__Config.js**:
```javascript
export const Endpoints__Config = { /* 9 endpoints */ };
export const Endpoints__Utils = { /* helper functions */ };
```

**API__Client.js**:
```javascript
export class API__Client { /* HTTP client */ }
export const apiClient = new API__Client();  // Singleton instance
```

**Transformation__Selector.js**:
```javascript
export class Transformation__Selector extends HTMLElement { /* component */ }
customElements.define('transformation-selector', Transformation__Selector);
```

### HTML Script Tags

**Module scripts** (v0.1.2):
```html
<script type="module" src="./js/playground.js"></script>
```

**Regular scripts** (v0.1.1 components):
```html
<script src="../v0.1.1/components/html-input/html-input.js"></script>
```

## 🐛 Bug Fixes

### 1. Timing Issue with Initial HTML ✅
**Problem**: Transform button didn't work on page load  
**Cause**: Event fired before listener attached  
**Fix**: Read initial textarea value after attaching listener

```javascript
// Read initial value (in case sample already loaded)
const textarea = html_input.querySelector('textarea');
if (textarea && textarea.value) {
    current_html = textarea.value;
}

// Then attach listener for future changes
document.addEventListener('html-changed', (e) => {
    current_html = e.detail.html;
});
```

### 2. Duplicate Dropdown Options ✅
**Problem**: Dropdown showed duplicate headers  
**Cause**: Template had hardcoded optgroups + dynamic generation  
**Fix**: Clear selector completely before populating

```javascript
selector.innerHTML = '<option value="">-- Select Transformation --</option>';
// Then add dynamic optgroups
```

### 3. Path Format Inconsistency ✅
**Problem**: `/html/to__dict` vs `/html/to/dict`  
**Fix**: Standardized on `/html/to/dict` in config

### 4. Missing Error Context ✅
**Problem**: Generic error messages  
**Fix**: Include endpoint display name in all errors

```javascript
throw new Error(`API Error [HTML → Dict] 500: Invalid HTML`);
```

## 📝 IFD Compliance

✅ **Version Independence**: v0.1.2 contains ONLY new/changed files  
✅ **File References**: Uses `../v0.1.1/` paths for unchanged components  
✅ **No Copying**: Zero files copied between versions  
✅ **Progressive**: Builds incrementally on v0.1.1  
✅ **Potentially Shippable**: Fully functional standalone  

---

## 🎨 Code Style

### Naming Conventions (osbot-utils style)

- **Classes**: `API__Client`, `Transformation__Selector` (double underscore namespace)
- **Functions**: `call_endpoint`, `build_payload` (snake_case)
- **Variables**: `current_html`, `endpoint_config` (snake_case)
- **Constants**: `Endpoints__Config` (capitalized with double underscore)

### Code Alignment

```javascript
const config = {
    endpoint_id : endpoint_id      ,  // Aligned colons
    route       : endpoint.route   ,  // Aligned commas
    input_type  : endpoint.input_type // Aligned values
};
```

### Inline Comments

```javascript
this.base_url = window.location.origin;  // Same server, no CORS issues
```