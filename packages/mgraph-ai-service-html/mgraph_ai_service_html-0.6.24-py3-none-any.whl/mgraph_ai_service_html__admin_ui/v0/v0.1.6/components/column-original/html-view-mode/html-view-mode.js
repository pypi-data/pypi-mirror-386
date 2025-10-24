/**
 * HTML View Mode Component - v0.1.6 (Refactored with ComponentUtils)
 * View mode with syntax highlighting
 */

import { ComponentUtils      } from '../../../../v0.1.6/utils/ComponentUtils.js';
import { Syntax__Highlighter } from '../../../../v0.1.4/js/utils/Syntax__Highlighter.js';

class HtmlViewMode extends HTMLElement {
    constructor() {
        super();
        console.log('👁️ HtmlViewMode constructor');
        this.htmlContent = '';
        this.templateLoaded = false;
    }

    async connectedCallback() {
        ComponentUtils.loadStyles(
            'html-view-mode-styles',
            '../v0.1.6/components/column-original/html-view-mode/html-view-mode.css'
        );

        this.templateLoaded = await ComponentUtils.loadTemplate(
            this,
            '../v0.1.6/components/column-original/html-view-mode/html-view-mode.html'
        );

        if (this.templateLoaded) {
            this.render();
        }
    }

    render() {
        const output = ComponentUtils.$(this, '#syntax-output');
        if (!output) return;

        if (!this.htmlContent.trim()) {
            output.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">👁️</div>
                    <div class="empty-state-text">Syntax-highlighted HTML will appear here</div>
                </div>
            `;
            return;
        }

        const highlighted = Syntax__Highlighter.highlight(this.htmlContent, 'html');
        output.innerHTML = `<pre class="syntax-output">${highlighted}</pre>`;
        console.log('👁️ HtmlViewMode: Syntax highlighting applied');
    }

    // Public API
    setHtml(html) {
        this.htmlContent = html;
        if (this.templateLoaded) {
            this.render();
        }
    }

    getHtml() {
        return this.htmlContent;
    }

    clear() {
        this.htmlContent = '';
        this.render();
    }
}

customElements.define('html-view-mode', HtmlViewMode);
console.log('✅ HtmlViewMode component registered (with ComponentUtils)');