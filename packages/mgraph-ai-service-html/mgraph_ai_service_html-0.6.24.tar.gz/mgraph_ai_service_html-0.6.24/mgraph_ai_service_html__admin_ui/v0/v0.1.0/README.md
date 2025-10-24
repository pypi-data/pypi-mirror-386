# HTML Service Admin UI - v0.1.0 (Foundation)

**Version**: v0.1.0  
**Status**: ✅ Complete  
**Type**: Major Version (Complete standalone implementation)

---

## Overview

This is the **foundation version** of the HTML Service Admin UI. It provides a complete dashboard interface for exploring and understanding the HTML transformation service capabilities.

### What's Included

✅ **Dashboard Page** (`index.html`)  
   - Service overview and statistics
   - Complete endpoint listing with descriptions
   - Quick action cards
   - Sample file showcase

✅ **Common Styles** (`css/common.css`)  
   - Gradient theme system
   - Reusable card components
   - Button styles and utilities
   - Responsive grid system

✅ **Dashboard Styles** (`css/dashboard.css`)  
   - Dashboard-specific layouts
   - Hero section
   - Stats grid
   - Endpoint list styling

✅ **API Client Service** (`js/services/api-client.js`)  
   - Centralized API communication
   - Endpoint configuration
   - Error handling
   - Response parsing
   - Performance metrics

✅ **Dashboard Logic** (`js/dashboard.js`)  
   - Endpoint display
   - Sample card handlers
   - Statistics updates
   - Toast notifications

✅ **Sample Files** (`samples/`)  
   - `simple.html` - Minimal structure (~15 text nodes, depth 5)
   - `complex.html` - Deeply nested (100+ text nodes, depth 15+)
   - `dashboard.html` - Self-referential placeholder

✅ **Error Page** (`404.html`)  
   - User-friendly 404 page
   - Navigation back to dashboard

---

## Usage

### Access the Dashboard

Navigate to: `/html-service/v0/v0.1.0/index.html`

The dashboard will load with:
- Service statistics
- Available endpoints
- Sample files
- Quick actions

### Explore Endpoints

All available API endpoints are listed on the dashboard with:
- HTTP method (POST/GET)
- Endpoint path
- Description
- Copy functionality

### View Samples

Click on any sample card to view the sample HTML in a new window:
- **Simple**: Basic testing
- **Complex**: Stress testing  
- **Dashboard**: Self-referential (placeholder)

---

## Architecture

### Zero Dependencies

This version uses **only native web platform features**:
- ✅ ES6+ JavaScript
- ✅ CSS3 with custom properties
- ✅ Fetch API
- ✅ DOM manipulation
- ❌ No React, Vue, Angular, jQuery, or any frameworks
- ❌ No build tools or bundlers

### File Organization

```
v0.1.0/
├── index.html              # Dashboard page (entry point)
├── 404.html                # Error page
├── README.md               # This file
├── css/
│   ├── common.css          # Shared styles (gradient theme, cards, buttons)
│   └── dashboard.css       # Dashboard-specific styles
├── js/
│   ├── services/
│   │   └── api-client.js   # API communication service
│   └── dashboard.js        # Dashboard page logic
└── samples/
    ├── simple.html         # Minimal sample
    ├── complex.html        # Nested sample
    └── dashboard.html      # Self-referential placeholder
```

### Key Components

**API Client** (`api-client.js`):
- Global instance: `window.apiClient`
- Methods: `callEndpoint()`, `loadSample()`, `callWithMetrics()`
- Endpoint registry with full configuration

**Dashboard** (`dashboard.js`):
- Initializes on `DOMContentLoaded`
- Populates endpoints from API client
- Handles sample viewing
- Updates statistics

**Common Styles** (`common.css`):
- CSS custom properties for theming
- Reusable component classes
- Responsive utilities
- Gradient background system

---

## Available Endpoints

### HTML Routes (`/html/*`)
- `POST /html/to__dict` - Parse HTML to dictionary
- `POST /html/to__html` - Round-trip validation
- `POST /html/to__text__nodes` - Extract text nodes with hashes
- `POST /html/to__lines` - Format as lines
- `POST /html/to__html__hashes` - Replace text with hashes
- `POST /html/to__html__xxx` - Privacy masking

### Dict Routes (`/dict/*`)
- `POST /dict/to__html` - Reconstruct HTML
- `POST /dict/to__text__nodes` - Extract text nodes from dict
- `POST /dict/to__lines` - Format dict as lines

### Hashes Routes (`/hashes/*`)
- `POST /hashes/to__html` - Apply hash mapping
