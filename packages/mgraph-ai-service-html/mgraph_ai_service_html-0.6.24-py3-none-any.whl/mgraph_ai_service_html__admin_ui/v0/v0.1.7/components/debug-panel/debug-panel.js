/**
 * Debug Panel Component - v0.1.7 (Top-right, collapsible)
 * Clean implementation with external template
 */

import { ComponentUtils } from '../../../v0.1.6/utils/ComponentUtils.js';

class DebugPanel extends HTMLElement {
    static TEMPLATE_PATH = '../v0.1.7/components/debug-panel/debug-panel.html';

    constructor() {
        super();
        console.log('🔧 DebugPanel constructor (v0.1.7)');
        this.collapsed = true;
    }

    async connectedCallback() {
        // Load v0.1.7 styles
        ComponentUtils.loadStyles(
            'debug-panel-styles-v017',
            '../v0.1.7/components/debug-panel/debug-panel.css'
        );

        // Load template
        await ComponentUtils.loadTemplate(this, DebugPanel.TEMPLATE_PATH);

        // Attach listeners
        this.attachListeners();
    }

    attachListeners() {
        // Toggle button
        const toggleBtn = ComponentUtils.$(this, '.debug-panel-toggle');
        const panel = ComponentUtils.$(this, '.debug-panel');
        const toggleIcon = ComponentUtils.$(this, '.toggle-icon');

        if (toggleBtn && panel) {
            ComponentUtils.on(toggleBtn, 'click', () => {
                this.collapsed = !this.collapsed;

                if (this.collapsed) {
                    panel.classList.remove('expanded');
                    panel.classList.add('collapsed');
                    if (toggleIcon) toggleIcon.textContent = '▼';
                } else {
                    panel.classList.remove('collapsed');
                    panel.classList.add('expanded');
                    if (toggleIcon) toggleIcon.textContent = '▲';
                }

                console.log(`🔧 DebugPanel: ${this.collapsed ? 'Collapsed' : 'Expanded'}`);
            });
        }

        // Action buttons
        this.querySelectorAll('[data-action]').forEach(btn => {
            ComponentUtils.on(btn, 'click', (e) => {
                const action = e.currentTarget.dataset.action;
                console.log(`🔧 DebugPanel: Action ${action}`);

                ComponentUtils.emitEvent(this, 'debug-action', { action });
            });
        });

        console.log('🔧 DebugPanel: Listeners attached');
    }
}

customElements.define('debug-panel', DebugPanel);
console.log('✅ DebugPanel component registered (v0.1.7 - collapsible)');