/**
 * Column Original Component - v0.1.6 (Refactored with ComponentUtils)
 * Orchestrates: column-header, sample-selector, html-edit-mode, html-view-mode
 *
 * Emits:
 *   html-changed - { html: string }
 *   clear-requested - {}
 */

import { ComponentUtils } from '../../utils/ComponentUtils.js';

class ColumnOriginal extends HTMLElement {
    constructor() {
        super();
        console.log('📝 ColumnOriginal constructor (refactored)');
        this.mode = 'view'; // 'edit' | 'view'
        this.templateLoaded = false;
    }

    async connectedCallback() {
        ComponentUtils.loadStyles(
            'column-original-styles',
            '../v0.1.6/components/column-original/column-original.css'
        );

        this.templateLoaded = await ComponentUtils.loadTemplate(
            this,
            '../v0.1.6/components/column-original/column-original.html'
        );

        if (this.templateLoaded) {
            this.attachListeners();
        }
    }

    attachListeners() {
        // Listen to sample selection
        this.addEventListener('sample-selected', (e) => {
            const { sampleContent } = e.detail;
            this.setHtml(sampleContent);
        });

        // Listen to HTML changes from edit mode
        this.addEventListener('html-changed', (e) => {
            console.log('📝 ColumnOriginal: HTML changed');
        });

        // Listen to mode changes
        this.addEventListener('mode-selected', (e) => {
            if (e.detail.columnId === 'original') {
                this.switchMode(e.detail.mode);
            }
        });

        // Clear button
        const clearBtn = ComponentUtils.$(this, '#btn-clear');
        ComponentUtils.on(clearBtn, 'click', () => {
            this.clear();
        });
    }

    switchMode(mode) {
        console.log(`📝 ColumnOriginal: Switching to ${mode} mode`);
        this.mode = mode;

        // Update column data-mode attribute
        const column = ComponentUtils.$(this, '.column');
        column?.setAttribute('data-mode', mode);

        // Update header
        const header = ComponentUtils.$(this, 'column-header');
        header?.setAttribute('active-mode', mode);

        // Show/hide mode containers
        const editContainer = ComponentUtils.$(this, '.mode-edit');
        const viewContainer = ComponentUtils.$(this, '.mode-view');

        if (mode === 'edit') {
            ComponentUtils.toggle(editContainer, true);
            ComponentUtils.toggle(viewContainer, false);
        } else {
            ComponentUtils.toggle(editContainer, false);
            ComponentUtils.toggle(viewContainer, true);

            // Sync content to view mode
            const editMode = ComponentUtils.$(this, 'html-edit-mode');
            const viewMode = ComponentUtils.$(this, 'html-view-mode');
            if (editMode && viewMode) {
                viewMode.setHtml(editMode.getHtml());
            }
        }
    }

    // Public API
    getHtml() {
        const editMode = ComponentUtils.$(this, 'html-edit-mode');
        return editMode ? editMode.getHtml() : '';
    }

    setHtml(html) {
        const editMode = ComponentUtils.$(this, 'html-edit-mode');
        const viewMode = ComponentUtils.$(this, 'html-view-mode');

        if (editMode) {
            editMode.setHtml(html);
        }

        if (viewMode && this.mode === 'view') {
            viewMode.setHtml(html);
        }
    }

    clear() {
        console.log('📝 ColumnOriginal: Clearing');

        const editMode = ComponentUtils.$(this, 'html-edit-mode');
        const viewMode = ComponentUtils.$(this, 'html-view-mode');
        const sampleSelector = ComponentUtils.$(this, 'sample-selector');

        if (editMode) editMode.clear();
        if (viewMode) viewMode.clear();
        if (sampleSelector) sampleSelector.reset();

        ComponentUtils.emitEvent(this, 'clear-requested');
    }

    loadSample(sampleName) {
        const sampleSelector = ComponentUtils.$(this, 'sample-selector');
        if (sampleSelector) {
            const select = ComponentUtils.$(sampleSelector, '#sample-select');
            if (select) {
                select.value = sampleName;
                select.dispatchEvent(new Event('change'));
            }
        }
    }
}

customElements.define('column-original', ColumnOriginal);
console.log('✅ ColumnOriginal component registered (refactored with ComponentUtils)');