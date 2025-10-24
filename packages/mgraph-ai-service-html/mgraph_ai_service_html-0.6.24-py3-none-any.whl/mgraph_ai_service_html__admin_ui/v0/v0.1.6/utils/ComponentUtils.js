/**
 * Component Utils - v0.1.6
 * Common utilities for Web Components
 *
 * Usage:
 *   await ComponentUtils.loadTemplate(this, 'path/to/template.html');
 *   ComponentUtils.loadStyles('style-id', 'path/to/styles.css');
 */

class ComponentUtils {
    /**
     * Load external HTML template into component
     * @param {HTMLElement} component - The component to load template into
     * @param {string} templatePath - Path to HTML template file
     * @returns {Promise<boolean>} Success status
     */
    static async loadTemplate(component, templatePath) {
        try {
            const response = await fetch(templatePath);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const html = await response.text();
            component.innerHTML = html;
            console.log(`✅ Template loaded: ${templatePath}`);
            return true;
        } catch (error) {
            console.error(`❌ Failed to load template: ${templatePath}`, error);
            component.innerHTML = '<div class="error">Failed to load template</div>';
            return false;
        }
    }

    /**
     * Load external CSS file (only once per styleId)
     * @param {string} styleId - Unique ID for this stylesheet
     * @param {string} stylePath - Path to CSS file
     */
    static loadStyles(styleId, stylePath) {
        if (!document.getElementById(styleId)) {
            const link = document.createElement('link');
            link.id = styleId;
            link.rel = 'stylesheet';
            link.href = stylePath;
            document.head.appendChild(link);
            console.log(`✅ Styles loaded: ${stylePath}`);
        }
    }

    /**
     * Load external CSS file into Shadow DOM
     * @param {ShadowRoot} shadowRoot - Shadow root to load styles into
     * @param {string} stylePath - Path to CSS file
     * @returns {HTMLLinkElement} The created link element
     */
    static loadShadowStyles(shadowRoot, stylePath) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = stylePath;
        shadowRoot.appendChild(link);
        console.log(`✅ Shadow styles loaded: ${stylePath}`);
        return link;
    }

    /**
     * Wait for component to be defined
     * @param {string} tagName - Component tag name
     * @returns {Promise<void>}
     */
    static async waitForComponent(tagName) {
        if (customElements.get(tagName)) {
            return;
        }
        await customElements.whenDefined(tagName);
    }

    /**
     * Dispatch custom event with detail
     * @param {HTMLElement} element - Element to dispatch from
     * @param {string} eventName - Event name
     * @param {*} detail - Event detail data
     * @param {boolean} bubbles - Should bubble (default: true)
     */
    static emitEvent(element, eventName, detail = null, bubbles = true) {
        const event = new CustomEvent(eventName, {
            detail,
            bubbles,
            composed: true
        });
        element.dispatchEvent(event);
        console.log(`📤 Event emitted: ${eventName}`, detail);
    }

    /**
     * Query selector with null safety
     * @param {HTMLElement} element - Element to query from
     * @param {string} selector - CSS selector
     * @returns {HTMLElement|null}
     */
    static $(element, selector) {
        return element.querySelector(selector);
    }

    /**
     * Query selector all with array return
     * @param {HTMLElement} element - Element to query from
     * @param {string} selector - CSS selector
     * @returns {Array<HTMLElement>}
     */
    static $$(element, selector) {
        return Array.from(element.querySelectorAll(selector));
    }

    /**
     * Add event listener with logging
     * @param {HTMLElement} element - Element to listen on
     * @param {string} eventName - Event name
     * @param {Function} handler - Event handler
     */
    static on(element, eventName, handler) {
        element?.addEventListener(eventName, handler);
    }

    /**
     * Set multiple attributes at once
     * @param {HTMLElement} element - Element to set attributes on
     * @param {Object} attrs - Key-value pairs of attributes
     */
    static setAttributes(element, attrs) {
        Object.entries(attrs).forEach(([key, value]) => {
            element.setAttribute(key, value);
        });
    }

    /**
     * Show/hide element
     * @param {HTMLElement} element - Element to toggle
     * @param {boolean} show - Show or hide
     */
    static toggle(element, show) {
        if (element) {
            element.style.display = show ? '' : 'none';
        }
    }

    /**
     * Debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function}
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Export for ES6 modules
export { ComponentUtils };

console.log('✅ ComponentUtils loaded');