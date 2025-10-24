/**
 * HTML Input Component
 * Provides textarea with sample selector and character counting
 */
class HtmlInput extends HTMLElement {
    constructor() {
        super();
        this.templateURL = '../v0.1.1/components/html-input/html-input.html';
        this.styleURL    = '../v0.1.1/components/html-input/html-input.css';
        this.state = {
            html: '',
            currentSample: ''
        };
    }

    async connectedCallback() {
        await this.loadStyles();
        await this.loadTemplate();
        this.attachEventListeners();
        this.loadDefaultSample();
    }

    async loadStyles() {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = this.styleURL;
        document.head.appendChild(link);
    }

    async loadTemplate() {
        const response = await fetch(this.templateURL);
        const html = await response.text();
        this.innerHTML = html;
    }

    attachEventListeners() {
        const textarea = this.querySelector('#html-textarea');
        const sampleSelector = this.querySelector('#sample-selector');
        const clearBtn = this.querySelector('#clear-btn');

        // Textarea changes
        textarea.addEventListener('input', () => {
            this.updateCharCount();
            this.state.html = textarea.value;
            this.emit('html-changed', { html: this.state.html });
        });

        // Sample selection
        sampleSelector.addEventListener('change', async (e) => {
            const sample = e.target.value;
            if (sample && sample !== 'custom') {
                await this.loadSample(sample);
            } else if (sample === 'custom') {
                textarea.value = '';
                this.updateCharCount();
            }
        });

        // Clear button
        clearBtn.addEventListener('click', () => {
            textarea.value = '';
            sampleSelector.value = 'custom';
            this.updateCharCount();
            this.emit('html-changed', { html: '' });
        });
    }

    async loadDefaultSample() {
        // Load 'simple' sample by default
        await this.loadSample('simple');
        const selector = this.querySelector('#sample-selector');
        selector.value = 'simple';
    }

    async loadSample(sampleName) {
        try {
            const response = await fetch(`../v0.1.1/samples/${sampleName}.html`);
            const html = await response.text();
            const textarea = this.querySelector('#html-textarea');
            textarea.value = html;
            this.state.html = html;
            this.state.currentSample = sampleName;
            this.updateCharCount();
            this.emit('html-changed', { html });
        } catch (error) {
            console.error('Failed to load sample:', error);
            alert('Failed to load sample file');
        }
    }

    updateCharCount() {
        const textarea = this.querySelector('#html-textarea');
        const charCount = this.querySelector('#char-count');
        const sizeWarning = this.querySelector('#size-warning');
        const length = textarea.value.length;
        
        charCount.textContent = `${length.toLocaleString()} characters`;
        
        // Show warning at 900KB (90% of 1MB limit)
        const MB_LIMIT = 1024 * 1024;
        if (length > MB_LIMIT * 0.9) {
            sizeWarning.style.display = 'inline';
        } else {
            sizeWarning.style.display = 'none';
        }
    }

    getValue() {
        return this.state.html;
    }

    emit(eventName, detail) {
        this.dispatchEvent(new CustomEvent(eventName, { 
            detail, 
            bubbles: true 
        }));
    }
}

customElements.define('html-input', HtmlInput);
