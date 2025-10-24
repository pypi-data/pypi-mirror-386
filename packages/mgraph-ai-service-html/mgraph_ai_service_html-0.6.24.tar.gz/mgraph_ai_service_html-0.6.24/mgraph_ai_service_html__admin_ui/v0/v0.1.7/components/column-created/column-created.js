/**
 * Column Created Component - v0.1.7
 * Orchestrates: column-header, html-view-mode, html-preview-mode (NEW)
 * Supports 3 modes: code, preview, split
 *
 * Emits:
 *   rebuild-requested - {}
 *   copy-requested - {}
 *   download-requested - {}
 */

import { ComponentUtils } from '../../../v0.1.6/utils/ComponentUtils.js';

class ColumnCreated extends HTMLElement {
    constructor() {
        super();
        console.log('✨ ColumnCreated constructor (v0.1.7)');
        this.mode = 'code'; // 'code' | 'preview' | 'split'
        this.currentHtml = '';
        this.templateLoaded = false;
    }

    async connectedCallback() {
        ComponentUtils.loadStyles(
            'column-created-styles',
            '../v0.1.7/components/column-created/column-created.css'
        );

        this.templateLoaded = await ComponentUtils.loadTemplate(
            this,
            '../v0.1.7/components/column-created/column-created.html'
        );

        if (this.templateLoaded) {
            setTimeout(() => this.attachListeners(), 0);
        }
    }

    attachListeners() {
        // Action buttons
        const rebuildBtn = ComponentUtils.$(this, '#btn-rebuild');
        const openWindowBtn = ComponentUtils.$(this, '#btn-open-window');
        const downloadBtn = ComponentUtils.$(this, '#btn-download');

        if (rebuildBtn) {
            ComponentUtils.on(rebuildBtn, 'click', () => {
                console.log('✨ ColumnCreated: Rebuild button clicked');
                ComponentUtils.emitEvent(this, 'rebuild-requested');
            });
        }

        if (openWindowBtn) {
            ComponentUtils.on(openWindowBtn, 'click', () => {
                console.log('✨ ColumnCreated: Open window button clicked');
                this.openInNewWindow();
            });
        }

        if (downloadBtn) {
            ComponentUtils.on(downloadBtn, 'click', () => {
                console.log('✨ ColumnCreated: Download button clicked');
                ComponentUtils.emitEvent(this, 'download-requested');
            });
        }

        // Mode change listener
        this.addEventListener('mode-selected', (e) => {
            if (e.detail.columnId === 'created') {
                this.switchMode(e.detail.mode);
            }
        });

        console.log('✨ ColumnCreated: All listeners attached');
    }

    switchMode(mode) {
        console.log(`✨ ColumnCreated: Switching to ${mode} mode`);
        this.mode = mode;

        // Update column data-mode attribute
        const column = ComponentUtils.$(this, '.created-column');
        column?.setAttribute('data-mode', mode);

        // Update header
        const header = ComponentUtils.$(this, 'column-header');
        header?.setAttribute('active-mode', mode);

        // Show/hide "Open in Window" button based on mode
        const openWindowBtn = ComponentUtils.$(this, '#btn-open-window');
        if (openWindowBtn) {
            // Show button only in preview and split modes
            ComponentUtils.toggle(openWindowBtn, mode === 'preview' || mode === 'split');
        }

        // Show/hide mode containers
        const codeContainer = ComponentUtils.$(this, '.mode-code');
        const previewContainer = ComponentUtils.$(this, '.mode-preview');
        const splitContainer = ComponentUtils.$(this, '.mode-split');

        ComponentUtils.toggle(codeContainer, mode === 'code');
        ComponentUtils.toggle(previewContainer, mode === 'preview');
        ComponentUtils.toggle(splitContainer, mode === 'split');

        // Sync content to newly visible components
        if (this.currentHtml) {
            this.updateVisibleComponents(this.currentHtml);
        }
    }

    /**
     * Update components based on current mode
     * @param {string} html - HTML content
     */
    updateVisibleComponents(html) {
        if (this.mode === 'code') {
            const codeView = ComponentUtils.$(this, '#created-html-view');
            if (codeView) {
                codeView.setHtml(html);
            }
        } else if (this.mode === 'preview') {
            const previewView = ComponentUtils.$(this, '#created-html-preview');
            if (previewView) {
                previewView.setHtml(html);
            }
        } else if (this.mode === 'split') {
            const codeView = ComponentUtils.$(this, '#created-html-view-split');
            const previewView = ComponentUtils.$(this, '#created-html-preview-split');

            if (codeView) {
                codeView.setHtml(html);
            }
            if (previewView) {
                previewView.setHtml(html);
            }
        }
    }

    /**
     * Public API: Set HTML content
     * @param {string} html - HTML content to display
     */
    setHtml(html) {
        console.log('✨ ColumnCreated: Setting HTML', html.length, 'characters');
        this.currentHtml = html;

        // Update ALL components (not just visible ones)
        // This ensures switching modes shows correct content
        const codeView = ComponentUtils.$(this, '#created-html-view');
        const previewView = ComponentUtils.$(this, '#created-html-preview');
        const codeViewSplit = ComponentUtils.$(this, '#created-html-view-split');
        const previewViewSplit = ComponentUtils.$(this, '#created-html-preview-split');

        if (codeView) {
            codeView.setHtml(html);
        }
        if (previewView) {
            previewView.setHtml(html);
        }
        if (codeViewSplit) {
            codeViewSplit.setHtml(html);
        }
        if (previewViewSplit) {
            previewViewSplit.setHtml(html);
        }
    }

    /**
     * Public API: Get current HTML
     * @returns {string}
     */
    getData() {
        return this.currentHtml;
    }

    /**
     * Open current HTML in new window
     */
    openInNewWindow() {
        if (!this.currentHtml) {
            console.warn('✨ ColumnCreated: No HTML to open in new window');
            return;
        }

        const newWindow = window.open('', '_blank', 'width=800,height=600');

        if (newWindow) {
            newWindow.document.open();
            newWindow.document.write(this.currentHtml);
            newWindow.document.close();
            console.log('✨ ColumnCreated: Opened HTML in new window');
        } else {
            console.error('✨ ColumnCreated: Failed to open new window (popup blocked?)');
            alert('Failed to open new window. Please allow popups for this site.');
        }
    }
}

customElements.define('column-created', ColumnCreated);
console.log('✅ ColumnCreated component registered (v0.1.7 - 3 modes)');