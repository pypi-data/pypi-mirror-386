/**
 * HTML Edit Mode Component - v0.1.6 (Refactored with ComponentUtils)
 * Edit mode with textarea and character count
 *
 * Emits:
 *   html-changed - { html: string }
 */

import { ComponentUtils } from '../../../../v0.1.6/utils/ComponentUtils.js';

class HtmlEditMode extends HTMLElement {
    constructor() {
        super();
        console.log('✏️ HtmlEditMode constructor');
        this.htmlContent = '';
        this.templateLoaded = false;
    }

    async connectedCallback() {
        ComponentUtils.loadStyles(
            'html-edit-mode-styles',
            '../v0.1.6/components/column-original/html-edit-mode/html-edit-mode.css'
        );

        this.templateLoaded = await ComponentUtils.loadTemplate(
            this,
            '../v0.1.6/components/column-original/html-edit-mode/html-edit-mode.html'
        );

        if (this.templateLoaded) {
            this.attachListeners();
            this.updateCharCount();
        }
    }

    attachListeners() {
        const textarea = ComponentUtils.$(this, '#html-textarea');
        ComponentUtils.on(textarea, 'input', () => {
            this.htmlContent = textarea.value;
            this.updateCharCount();
            this.emitHtmlChanged();
        });
    }

    updateCharCount() {
        const charCount = ComponentUtils.$(this, '#char-count');
        if (charCount) {
            charCount.textContent = this.htmlContent.length.toLocaleString();
        }
    }

    emitHtmlChanged() {
        ComponentUtils.emitEvent(this, 'html-changed', { html: this.htmlContent });
    }

    // Public API
    getHtml() {
        return this.htmlContent;
    }

    setHtml(html) {
        this.htmlContent = html;
        const textarea = ComponentUtils.$(this, '#html-textarea');
        if (textarea) {
            textarea.value = html;
        }
        this.updateCharCount();
        this.emitHtmlChanged();
    }

    clear() {
        this.setHtml('');
    }
}

customElements.define('html-edit-mode', HtmlEditMode);
console.log('✅ HtmlEditMode component registered (with ComponentUtils)');