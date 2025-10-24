/**
 * JSON Edit Mode Component - v0.1.6
 * Reusable JSON editor with validation
 *
 * Attributes:
 *   title - Display title
 *   icon - Emoji icon
 *   placeholder - Placeholder text
 *
 * Emits:
 *   json-changed - { json: object, isValid: boolean }
 */

import { ComponentUtils } from '../../../utils/ComponentUtils.js';

class JsonEditMode extends HTMLElement {
    constructor() {
        super();
        console.log('✏️ JsonEditMode constructor');
        this.jsonData = null;
        this.templateLoaded = false;
    }

    async connectedCallback() {
        ComponentUtils.loadStyles(
            'json-edit-mode-styles',
            '../v0.1.6/components/column-middle/json-edit-mode/json-edit-mode.css'
        );

        this.templateLoaded = await ComponentUtils.loadTemplate(
            this,
            '../v0.1.6/components/column-middle/json-edit-mode/json-edit-mode.html'
        );

        if (this.templateLoaded) {
            this.renderTitle();
            this.updatePlaceholder();
            this.attachListeners();
        }
    }

    renderTitle() {
        const title = this.getAttribute('title') || 'JSON Editor';
        const icon = this.getAttribute('icon') || '✏️';

        const header = ComponentUtils.$(this, '.json-edit-header');
        if (header) {
            header.innerHTML = `${icon} ${title}`;
        }
    }

    updatePlaceholder() {
        const placeholder = this.getAttribute('placeholder') || '{"key": "value"}';
        const textarea = ComponentUtils.$(this, '#json-textarea');
        if (textarea) {
            textarea.placeholder = placeholder;
        }
    }

    attachListeners() {
        const textarea = ComponentUtils.$(this, '#json-textarea');

        // Use blur to avoid constant parsing while typing
        ComponentUtils.on(textarea, 'blur', () => {
            this.handleChange();
        });

        // Also listen for manual trigger (e.g., when switching modes)
        ComponentUtils.on(textarea, 'input', () => {
            // Store raw text but don't parse yet
            this.rawText = textarea.value;
        });
    }

    handleChange() {
        const textarea = ComponentUtils.$(this, '#json-textarea');
        if (!textarea) return;

        const text = textarea.value.trim();

        if (!text) {
            this.jsonData = null;
            ComponentUtils.emitEvent(this, 'json-changed', {
                json: null,
                isValid: true
            });
            return;
        }

        try {
            this.jsonData = JSON.parse(text);

            // Remove error styling
            textarea.classList.remove('json-error');

            ComponentUtils.emitEvent(this, 'json-changed', {
                json: this.jsonData,
                isValid: true
            });

            console.log('✏️ JsonEditMode: Valid JSON parsed');
        } catch (e) {
            // Add error styling
            textarea.classList.add('json-error');

            ComponentUtils.emitEvent(this, 'json-changed', {
                json: null,
                isValid: false,
                error: e.message
            });

            console.warn('✏️ JsonEditMode: Invalid JSON', e.message);
        }
    }

    // Public API
    setData(data) {
        this.jsonData = data;
        const textarea = ComponentUtils.$(this, '#json-textarea');
        if (textarea && data) {
            textarea.value = JSON.stringify(data, null, 2);
            textarea.classList.remove('json-error');
        }
    }

    getData() {
        // Parse current textarea content before returning
        this.handleChange();
        return this.jsonData;
    }

    clear() {
        this.jsonData = null;
        const textarea = ComponentUtils.$(this, '#json-textarea');
        if (textarea) {
            textarea.value = '';
            textarea.classList.remove('json-error');
        }
    }
}

customElements.define('json-edit-mode', JsonEditMode);
console.log('✅ JsonEditMode component registered');