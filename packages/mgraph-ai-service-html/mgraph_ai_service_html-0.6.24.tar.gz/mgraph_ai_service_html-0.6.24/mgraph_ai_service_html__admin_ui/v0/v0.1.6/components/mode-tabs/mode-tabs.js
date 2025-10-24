/**
 * Mode Tabs Component - v0.1.6
 * Reusable Edit/View/Preview toggle tabs
 * 
 * Usage:
 *   <mode-tabs modes="edit,view" active="edit" column-id="original"></mode-tabs>
 * 
 * Emits:
 *   mode-selected - { mode: 'edit'|'view'|'preview', columnId: 'original'|'middle'|'created' }
 */

class ModeTabs extends HTMLElement {
    constructor() {
        super();
        console.log('🔧 ModeTabs constructor');
    }

    connectedCallback() {
        this.render();
    }

    // Attributes to observe
    static get observedAttributes() {
        return ['active'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'active' && oldValue !== newValue) {
            this.updateActiveTab();
        }
    }

    render() {
        const modes = (this.getAttribute('modes') || 'edit,view').split(',');
        const active = this.getAttribute('active') || modes[0];
        const columnId = this.getAttribute('column-id') || '';

        const modeIcons = {
            'edit': '✏️',
            'view': '👁️',
            'preview': '🌐'
        };

        const modeLabels = {
            'edit': 'Edit',
            'view': 'View',
            'preview': 'Preview'
        };

        this.innerHTML = `
            <div class="mode-tabs">
                ${modes.map(mode => `
                    <button 
                        class="mode-tab ${mode === active ? 'active' : ''}" 
                        data-mode="${mode}"
                        data-column-id="${columnId}"
                    >
                        ${modeIcons[mode]} ${modeLabels[mode]}
                    </button>
                `).join('')}
            </div>
        `;

        // Attach listeners AFTER innerHTML is set
        // Use setTimeout to ensure DOM is fully rendered
        setTimeout(() => this.attachListeners(), 0);
    }

    attachListeners() {
        this.querySelectorAll('.mode-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const mode = e.currentTarget.dataset.mode;
                const columnId = e.currentTarget.dataset.columnId;

                // Update active state
                this.setAttribute('active', mode);

                // Emit event
                this.dispatchEvent(new CustomEvent('mode-selected', {
                    detail: { mode, columnId },
                    bubbles: true,
                    composed: true // Allow event to cross Shadow DOM boundary
                }));

                console.log(`🔧 ModeTabs: Selected ${mode} for column ${columnId}`);
            });
        });

        console.log(`🔧 ModeTabs: Attached listeners to ${this.querySelectorAll('.mode-tab').length} tabs`);
    }

    updateActiveTab() {
        const active = this.getAttribute('active');
        this.querySelectorAll('.mode-tab').forEach(tab => {
            if (tab.dataset.mode === active) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
    }
}

customElements.define('mode-tabs', ModeTabs);
console.log('✅ ModeTabs component registered');