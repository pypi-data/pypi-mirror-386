/**
 * Sample Selector Component - v0.1.6 (Refactored with ComponentUtils)
 * Dropdown for selecting HTML samples
 *
 * Emits:
 *   sample-selected - { sampleName: string, sampleContent: string }
 */

import { ComponentUtils } from '../../../../v0.1.6/utils/ComponentUtils.js';
import { Samples        } from '../../../../v0.1.5/data/samples.js';

class SampleSelector extends HTMLElement {
    constructor() {
        super();
        console.log('📦 SampleSelector constructor');
    }

    connectedCallback() {
        this.render();
        this.attachListeners();

        ComponentUtils.loadStyles(
            'sample-selector-styles',
            '../v0.1.6/components/column-original/sample-selector/sample-selector.css'
        );
    }

    render() {
        this.innerHTML = `
            <div class="sample-selector-container">
                <select id="sample-select" class="sample-select">
                    <option value="">-- Select a Sample --</option>
                    <option value="micro">Micro HTML (Minimal)</option>
                    <option value="simple">Simple HTML</option>
                    <option value="complex">Complex HTML (Deep Nesting)</option>
                    <option value="custom">Custom (Paste Your Own)</option>
                </select>
            </div>
        `;
    }

    attachListeners() {
        const select = ComponentUtils.$(this, '#sample-select');
        ComponentUtils.on(select, 'change', (e) => {
            this.handleSampleChange(e.target.value);
        });
    }

    handleSampleChange(sampleName) {
        console.log(`📦 SampleSelector: Selected ${sampleName}`);

        if (!sampleName || sampleName === 'custom') {
            return;
        }

        const sampleContent = Samples[sampleName];
        if (sampleContent) {
            ComponentUtils.emitEvent(this, 'sample-selected', {
                sampleName,
                sampleContent
            });
        }
    }

    // Public API
    reset() {
        const select = ComponentUtils.$(this, '#sample-select');
        if (select) {
            select.value = 'custom';
        }
    }
}

customElements.define('sample-selector', SampleSelector);
console.log('✅ SampleSelector component registered (with ComponentUtils)');