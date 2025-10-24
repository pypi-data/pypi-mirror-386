/**
 * Syntax Highlighter Service - v0.1.4
 *
 * Lightweight syntax highlighting for JSON, HTML, and other formats
 * Zero external dependencies - pure JavaScript
 *
 * Usage:
 *   import { Syntax__Highlighter } from './js/utils/Syntax__Highlighter.js';
 *   Syntax__Highlighter.loadStyles(); // Call once per page
 *   const highlighted = Syntax__Highlighter.highlight(data, 'json');
 *   element.innerHTML = highlighted;
 */

class Syntax__Highlighter__Class {
    constructor() {
        /**
         * CSS file location (relative to this module)
         */
        this.styleURL = './css/syntax-highlighting.css';
        this.stylesLoaded = false;
    }

    /**
     * Main highlighting method - auto-detects or uses specified type
     * @param {*} data - Data to highlight
     * @param {string} type - 'json', 'html', or 'text'
     * @returns {string} HTML string with syntax highlighting
     */
    highlight(data, type = 'text') {
        switch (type) {
            case 'json':
                return this.highlightJSON(data);
            case 'html':
                return this.highlightHTML(data);
            case 'text':
            default:
                return this.escapeHtml(String(data));
        }
    }

    /**
     * Highlight JSON with color-coded syntax
     * @param {object|string} obj - JSON object or string
     * @returns {string} Highlighted HTML
     */
    highlightJSON(obj) {
        // Convert to string if object
        const json = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);

        return json
            // First escape HTML entities
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            // Highlight keys (property names)
            .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
            // Highlight string values
            .replace(/: "([^"]*?)"/g, ': <span class="json-string">"$1"</span>')
            // Highlight numbers (integers and decimals, including negative)
            .replace(/: (-?\d+\.?\d*)/g, ': <span class="json-number">$1</span>')
            // Highlight booleans and null
            .replace(/: (true|false|null)/g, ': <span class="json-boolean">$1</span>');
    }

    /**
     * Highlight HTML with color-coded syntax (Chrome DevTools style)
     * @param {string} html - HTML string
     * @returns {string} Highlighted HTML
     */
    highlightHTML(html) {
        return this.escapeHtml(html)
            // DOCTYPE declaration
            .replace(/(&lt;!DOCTYPE[^&]*?&gt;)/gi, '<span class="html-doctype">$1</span>')
            // Self-closing tags: <tag attr="value" />
            .replace(/(&lt;)([\w-]+)([^&]*?)(\/&gt;)/g, (match, lt, tag, attrs, close) => {
                let result = `<span class="html-punctuation">${lt}</span><span class="html-tag">${tag}</span>`;

                if (attrs) {
                    result += attrs.replace(/([\w-]+)(=)(".*?")/g,
                        '<span class="html-attr">$1</span><span class="html-punctuation">$2</span><span class="html-string">$3</span>');
                }

                result += `<span class="html-punctuation">${close}</span>`;
                return result;
            })
            // Opening tags with attributes: <tag attr="value">
            .replace(/(&lt;)([\w-]+)([^&]*?)(&gt;)/g, (match, lt, tag, attrs, gt) => {
                let result = `<span class="html-punctuation">${lt}</span><span class="html-tag">${tag}</span>`;

                if (attrs) {
                    result += attrs.replace(/([\w-]+)(=)(".*?")/g,
                        '<span class="html-attr">$1</span><span class="html-punctuation">$2</span><span class="html-string">$3</span>');
                }

                result += `<span class="html-punctuation">${gt}</span>`;
                return result;
            })
            // Closing tags: </tag>
            .replace(/(&lt;\/)([\w-]+)(&gt;)/g,
                '<span class="html-punctuation">$1</span><span class="html-tag">$2</span><span class="html-punctuation">$3</span>');
    }

    /**
     * Escape HTML entities to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Load CSS styles (call once per page)
     * Similar pattern to how other components load styles
     */
    loadStyles() {
        // Prevent double-loading
        if (this.stylesLoaded) {
            return;
        }

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = new URL(this.styleURL, import.meta.url).href;
        document.head.appendChild(link);

        this.stylesLoaded = true;
    }
}

// Export singleton instance - only one instance needed per page
export const Syntax__Highlighter = new Syntax__Highlighter__Class();