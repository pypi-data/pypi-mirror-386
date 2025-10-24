/**
 * HTML Preview Mode Component - v0.1.7
 * Renders HTML in an iframe for preview
 *
 * Public API:
 *   setHtml(html) - Render HTML in preview
 *   refresh() - Re-render current HTML
 *   openInNewWindow() - Open preview in new window
 */

import { ComponentUtils } from '../../../../v0.1.6/utils/ComponentUtils.js';

class HtmlPreviewMode extends HTMLElement {
    constructor() {
        super();
        console.log('🖼️ HtmlPreviewMode constructor');
        this.currentHtml = '';
    }

    async connectedCallback() {
        // Load styles
        ComponentUtils.loadStyles(
            'html-preview-mode-styles',
            '../v0.1.7/components/column-created/html-preview-mode/html-preview-mode.css'
        );

        // Load template
        await ComponentUtils.loadTemplate(
            this,
            '../v0.1.7/components/column-created/html-preview-mode/html-preview-mode.html'
        );

        // Wait for DOM to be ready
        setTimeout(() => this.attachListeners(), 0);
    }

    attachListeners() {
        // No controls in this component anymore
        // "Open in New Window" button is now in column-header
        console.log('🖼️ HtmlPreviewMode: Ready (no controls)');
    }

    /**
     * Set HTML content and render in iframe
     * @param {string} html - HTML content to preview
     */
    setHtml(html) {
        this.currentHtml = html;

        if (!html || html.trim() === '') {
            this.showEmptyState();
            return;
        }

        this.hideEmptyState();
        this.renderInIframe(html);
    }

    /**
     * Render HTML in the iframe
     * @param {string} html - HTML content
     */
    renderInIframe(html) {
        const iframe = ComponentUtils.$(this, '.preview-frame');

        if (!iframe) {
            console.error('🖼️ Preview iframe not found');
            return;
        }

        try {
            const doc = iframe.contentDocument || iframe.contentWindow.document;

            // Clear existing content
            doc.open();

            // Write new HTML
            doc.write(html);

            // Close document to finish loading
            doc.close();

            console.log('🖼️ HTML rendered in preview');
        } catch (error) {
            console.error('🖼️ Failed to render HTML:', error);
            this.showError(error.message);
        }
    }

    /**
     * Refresh the current preview
     */
    refresh() {
        console.log('🖼️ Refreshing preview');
        if (this.currentHtml) {
            this.renderInIframe(this.currentHtml);
        }
    }

    /**
     * Open preview in a new window
     */
    openInNewWindow() {
        if (!this.currentHtml) {
            console.warn('🖼️ No HTML to open in new window');
            return;
        }

        const newWindow = window.open('', '_blank', 'width=800,height=600');

        if (newWindow) {
            newWindow.document.open();
            newWindow.document.write(this.currentHtml);
            newWindow.document.close();
            console.log('🖼️ Opened preview in new window');
        } else {
            console.error('🖼️ Failed to open new window (popup blocked?)');
            alert('Failed to open new window. Please allow popups for this site.');
        }
    }

    /**
     * Show empty state
     */
    showEmptyState() {
        const emptyState = ComponentUtils.$(this, '.empty-state');
        const frameWrapper = ComponentUtils.$(this, '.preview-frame-wrapper');

        ComponentUtils.toggle(emptyState, true);
        ComponentUtils.toggle(frameWrapper, false);
    }

    /**
     * Hide empty state
     */
    hideEmptyState() {
        const emptyState = ComponentUtils.$(this, '.empty-state');
        const frameWrapper = ComponentUtils.$(this, '.preview-frame-wrapper');

        ComponentUtils.toggle(emptyState, false);
        ComponentUtils.toggle(frameWrapper, true);
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        const iframe = ComponentUtils.$(this, '.preview-frame');

        if (iframe) {
            const doc = iframe.contentDocument || iframe.contentWindow.document;
            doc.open();
            doc.write(`
                <html>
                <head>
                    <style>
                        body {
                            font-family: system-ui, -apple-system, sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            margin: 0;
                            background: #fef2f2;
                            color: #991b1b;
                        }
                        .error-box {
                            text-align: center;
                            padding: 2rem;
                            border-radius: 8px;
                            background: white;
                            border: 2px solid #ef4444;
                        }
                        .error-icon {
                            font-size: 3rem;
                            margin-bottom: 1rem;
                        }
                        h2 {
                            margin: 0 0 0.5rem 0;
                            font-size: 1.25rem;
                        }
                        p {
                            margin: 0;
                            font-size: 0.875rem;
                            color: #dc2626;
                        }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <div class="error-icon">⚠️</div>
                        <h2>Preview Error</h2>
                        <p>${message}</p>
                    </div>
                </body>
                </html>
            `);
            doc.close();
        }
    }

    /**
     * Get current HTML
     * @returns {string}
     */
    getHtml() {
        return this.currentHtml;
    }
}

customElements.define('html-preview-mode', HtmlPreviewMode);
console.log('✅ HtmlPreviewMode component registered');