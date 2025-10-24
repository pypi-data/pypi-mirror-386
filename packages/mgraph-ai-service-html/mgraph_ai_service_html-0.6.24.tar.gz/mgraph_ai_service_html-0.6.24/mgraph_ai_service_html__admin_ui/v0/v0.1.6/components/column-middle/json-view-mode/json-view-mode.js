/**
 * JSON View Mode Component - v0.1.6
 * Reusable JSON viewer with syntax highlighting
 *
 * Attributes:
 *   title - Display title
 *   icon - Emoji icon
 *   empty-text - Text to show when empty
 */

import { ComponentUtils } from '../../../../v0.1.6/utils/ComponentUtils.js';
import { Syntax__Highlighter } from '../../../../v0.1.4/js/utils/Syntax__Highlighter.js';

class JsonViewMode extends HTMLElement {
    constructor() {
        super();
        console.log('📋 JsonViewMode constructor');
        this.jsonData = null;
        this.templateLoaded = false;
    }

    async connectedCallback() {
        ComponentUtils.loadStyles( 'json-view-mode-styles',
                                   '../v0.1.6/components/column-middle/json-view-mode/json-view-mode.css');

        this.templateLoaded = await ComponentUtils.loadTemplate(this,
                                                                '../v0.1.6/components/column-middle/json-view-mode/json-view-mode.html');

        if (this.templateLoaded) {
            this.renderTitle();
            this.render();
        }
    }

    renderTitle() {
        const title = this.getAttribute('title') || 'JSON Data';
        const icon = this.getAttribute('icon') || '📋';

        const header = ComponentUtils.$(this, '.json-view-header');
        if (header) {
            header.innerHTML = `${icon} ${title}`;
        }
    }

    render() {
        const output = ComponentUtils.$(this, '#json-output');
        if (!output) return;

        if (!this.jsonData) {
            const emptyText = this.getAttribute('empty-text') || 'JSON data will appear here';
            const icon = this.getAttribute('icon') || '📋';

            output.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">${icon}</div>
                    <div class="empty-state-text">${emptyText}</div>
                </div>
            `;
            return;
        }

        const highlighted = Syntax__Highlighter.highlight(this.jsonData, 'json');
        output.innerHTML = `<pre class="syntax-output">${highlighted}</pre>`;
        console.log('📋 JsonViewMode: JSON rendered with syntax highlighting');
    }

    // Public API
    setData(data) {
        this.jsonData = data;
        if (this.templateLoaded) {
            this.render();
        }
    }

    getData() {
        return this.jsonData;
    }

    clear() {
        this.jsonData = null;
        this.render();
    }
}

customElements.define('json-view-mode', JsonViewMode);
console.log('✅ JsonViewMode component registered');