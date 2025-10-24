/**
 * Playground Logic - v0.1.5
 * 3-Column Architecture: Original HTML | Layout & Content Objects | Created HTML
 *
 * IFD COMPLIANT: Web Component architecture
 */

// Import samples
import { Samples } from '../../../v0.1.5/data/samples.js';

// Import config from v0.1.3 (reuse)
import { Endpoints__Config } from '../../../v0.1.3/js/config/Endpoints__Config.js';

// Import syntax highlighter from v0.1.4 (reuse)
import { Syntax__Highlighter } from '../../../v0.1.4/js/utils/Syntax__Highlighter.js';

/**
 * Playground Controller Component
 * Web Component that manages the entire playground
 */
class PlaygroundController extends HTMLElement {
    constructor() {
        super();
        console.log('🎮 PlaygroundController constructor called');

        // State
        this.currentDict = null;
        this.currentHashes = null;
        this.currentCreatedHtml = null;

        // Load syntax highlighter styles
        Syntax__Highlighter.loadStyles();
    }

    connectedCallback() {
        console.log('🎮 PlaygroundController connectedCallback - component mounted!');

        // Get DOM references
        this.getDOMReferences();

        // Attach event listeners
        this.attachEventListeners();

        console.log('✅ Event listeners attached');

        // Auto-run full flow on load
        console.log('🚀 Running auto-flow: Load Micro → Parse → Rebuild');
        setTimeout(() => {
            this.runFullFlow();
        }, 500);
    }

    disconnectedCallback() {
        console.log('🎮 PlaygroundController disconnected');
        // Cleanup if needed
    }

    /**
     * Get all DOM element references
     */
    getDOMReferences() {
        // Input elements
        this.htmlInput = document.getElementById('html-input');
        this.sampleSelector = document.getElementById('sample-selector');
        this.charCount = document.getElementById('char-count');

        // Middle column outputs
        this.dictOutput = document.getElementById('dict-output');
        this.hashesOutput = document.getElementById('hashes-output');

        // Right column output
        this.createdHtmlOutput = document.getElementById('created-html-output');
        this.statusMessage = document.getElementById('status-message');

        // Buttons
        this.btnClearInput = document.getElementById('btn-clear-input');
        this.btnTransformParse = document.getElementById('btn-transform-parse');
        this.btnTransformRebuild = document.getElementById('btn-transform-rebuild');
        this.btnCopyOutput = document.getElementById('btn-copy-output');
        this.btnDownloadOutput = document.getElementById('btn-download-output');

        // Debug buttons
        this.debugLoadMicro = document.getElementById('debug-load-micro');
        this.debugLoadSimple = document.getElementById('debug-load-simple');
        this.debugParse = document.getElementById('debug-parse');
        this.debugRebuild = document.getElementById('debug-rebuild');
        this.debugFullFlow = document.getElementById('debug-full-flow');

        console.log('✅ DOM references obtained');
    }

    /**
     * Attach all event listeners
     */
    attachEventListeners() {
        // Input events
        this.htmlInput?.addEventListener('input', () => this.updateCharCount());
        this.sampleSelector?.addEventListener('change', (e) => this.loadSample(e.target.value));

        // Button events
        this.btnClearInput?.addEventListener('click', () => this.clearInput());
        this.btnTransformParse?.addEventListener('click', () => this.parseHtml());
        this.btnTransformRebuild?.addEventListener('click', () => this.rebuildHtml());
        this.btnCopyOutput?.addEventListener('click', () => this.copyOutput());
        this.btnDownloadOutput?.addEventListener('click', () => this.downloadOutput());

        // Debug button listeners
        this.debugLoadMicro?.addEventListener('click', () => this.loadSample('micro'));
        this.debugLoadSimple?.addEventListener('click', () => this.loadSample('simple'));
        this.debugParse?.addEventListener('click', () => this.parseHtml());
        this.debugRebuild?.addEventListener('click', () => this.rebuildHtml());
        this.debugFullFlow?.addEventListener('click', () => this.runFullFlow());
    }

    /**
     * Run full flow: Load → Parse → Rebuild
     */
    async runFullFlow() {
        console.log('⚡ Starting full flow...');

        // Step 1: Load micro sample
        this.loadSample('micro');
        await this.delay(300);

        // Step 2: Parse
        await this.parseHtml();
        await this.delay(300);

        // Step 3: Rebuild
        await this.rebuildHtml();

        console.log('✅ Full flow complete!');
    }

    /**
     * Helper: delay function
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Update character count
     */
    updateCharCount() {
        const count = this.htmlInput.value.length;
        this.charCount.textContent = count.toLocaleString();
    }

    /**
     * Load sample HTML
     */
    loadSample(sampleName) {
        console.log(`📄 Loading sample: ${sampleName}`);

        if (!sampleName || sampleName === 'custom') {
            return;
        }

        const sample = Samples[sampleName];
        if (sample) {
            this.htmlInput.value = sample;
            this.sampleSelector.value = sampleName;
            this.updateCharCount();
            console.log(`✅ Sample loaded: ${sample.length} characters`);
        } else {
            console.error(`❌ Sample not found: ${sampleName}`);
        }
    }

    /**
     * Clear input
     */
    clearInput() {
        this.htmlInput.value = '';
        this.updateCharCount();
        this.sampleSelector.value = 'custom';
    }

    /**
     * Parse HTML → Dict + Hashes
     * Using the combined endpoint that returns both in the correct format
     */
    async parseHtml() {
        const html = this.htmlInput.value.trim();

        console.log('🔍 Parse requested...');

        if (!html) {
            this.showStatus('error', 'Please enter some HTML to parse');
            console.warn('⚠️ No HTML to parse');
            return;
        }

        this.showStatus('loading', 'Parsing HTML...');
        console.log(`📤 Sending ${html.length} characters to API...`);

        try {
            // Use the combined endpoint that returns dict with hashes + hash_mapping
            // This endpoint is not in v0.1.3 config but exists on the server
            console.log('🌐 Calling combined dict/hashes endpoint...');

            const url = '/html/to/dict/hashes';
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    html: html,
                    max_depth: 256
                })
            });

            console.log(`   Response status: ${response.status}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`   Error: ${errorText}`);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const result = await response.json();
            console.log('📥 API response received:', result);

            // Extract the data
            // Response structure:
            // {
            //   html_dict: { tag, attrs, nodes: [{ type: "TEXT", data: "hash_id" }] },
            //   hash_mapping: { "hash_id": "actual text" },
            //   node_count, max_depth, total_text_hashes, max_depth_reached
            // }
            this.currentDict = result.html_dict;
            this.currentHashes = result.hash_mapping;

            console.log('Extracted dict:', this.currentDict);
            console.log('Extracted hash_mapping:', this.currentHashes);

            // Display results with syntax highlighting
            this.dictOutput.innerHTML = `<pre class="syntax-output">${Syntax__Highlighter.highlight(result.html_dict, 'json')}</pre>`;
            this.hashesOutput.innerHTML = `<pre class="syntax-output">${Syntax__Highlighter.highlight(result.hash_mapping, 'json')}</pre>`;

            this.showStatus('success', 'HTML parsed successfully!');
            console.log('✅ Parse complete!');

        } catch (error) {
            this.showStatus('error', `Parse failed: ${error.message}`);
            console.error('❌ Parse error:', error);
        }
    }

    /**
     * Rebuild HTML from Dict + Hashes
     */
    async rebuildHtml() {
        console.log('🔧 Rebuild requested...');

        if (!this.currentDict || !this.currentHashes) {
            this.showStatus('error', 'Please parse HTML first to generate Dict and Hashes');
            console.warn('⚠️ No Dict/Hashes available');
            return;
        }

        this.showStatus('loading', 'Rebuilding HTML...');
        console.log('📤 Sending Dict + Hashes to API...');

        try {
            // Call the reconstruction endpoint
            // Using v0.1.3 endpoint ID: 'hashes-to-html'
            const payload = {
                html_dict: this.currentDict,
                hash_mapping: this.currentHashes
            };

            console.log('🌐 Calling reconstruction endpoint...');
            console.log('   Payload:', payload);

            const url = '/hashes/to/html';
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            console.log(`   Response status: ${response.status}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`   Error: ${errorText}`);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            // The response is HTML text, not JSON!
            const htmlResult = await response.text();
            console.log('📥 Rebuild response received (HTML):', htmlResult.substring(0, 100) + '...');

            // Store result
            this.currentCreatedHtml = htmlResult;

            // Display result with syntax highlighting
            this.createdHtmlOutput.innerHTML = `<pre class="syntax-output">${Syntax__Highlighter.highlight(htmlResult, 'html')}</pre>`;

            this.showStatus('success', 'HTML rebuilt successfully!');
            console.log('✅ Rebuild complete!');

        } catch (error) {
            this.showStatus('error', `Rebuild failed: ${error.message}`);
            console.error('❌ Rebuild error:', error);
        }
    }

    /**
     * Copy output to clipboard
     */
    async copyOutput() {
        if (!this.currentCreatedHtml) {
            this.showStatus('error', 'No output to copy');
            return;
        }

        try {
            await navigator.clipboard.writeText(this.currentCreatedHtml);
            this.showStatus('success', 'Copied to clipboard!');
        } catch (error) {
            this.showStatus('error', 'Failed to copy to clipboard');
            console.error('Copy error:', error);
        }
    }

    /**
     * Download output as HTML file
     */
    downloadOutput() {
        if (!this.currentCreatedHtml) {
            this.showStatus('error', 'No output to download');
            return;
        }

        const blob = new Blob([this.currentCreatedHtml], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'reconstructed.html';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showStatus('success', 'Download started!');
    }

    /**
     * Show status message
     */
    showStatus(type, message) {
        this.statusMessage.className = `status-message status-${type}`;
        this.statusMessage.textContent = message;
        this.statusMessage.style.display = 'block';

        // Auto-hide after 3 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                this.statusMessage.style.display = 'none';
            }, 3000);
        }
    }

    /**
     * Call API endpoint
     */
    async callEndpoint(endpointKey, payload) {
        console.log(`🌐 API Call: ${endpointKey}`);
        console.log(`   Config object:`, Endpoints__Config);

        // v0.1.3 Endpoints__Config is the direct object, not nested
        const endpoint = Endpoints__Config[endpointKey];

        if (!endpoint) {
            console.error(`❌ Endpoint not found: ${endpointKey}`);
            console.error(`   Available endpoints:`, Object.keys(Endpoints__Config));
            throw new Error(`Endpoint "${endpointKey}" not found`);
        }

        // Use the route directly - the service is already mounted correctly
        // Don't add /html-service/v0 prefix!
        const url = endpoint.route;
        const method = endpoint.method || 'POST';

        console.log(`   URL: ${url}`);
        console.log(`   Method: ${method}`);
        console.log(`   Endpoint config:`, endpoint);

        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (method === 'POST') {
            // Determine payload format based on endpoint
            if (endpointKey === 'dict-and-nodes-to-html' || endpointKey === 'hashes-to-html') {
                // These endpoints expect the payload as-is
                options.body = JSON.stringify(payload);
            } else {
                // HTML transformation endpoints expect { html: "..." }
                options.body = JSON.stringify({ html: payload });
            }
            console.log(`   Payload size: ${options.body.length} bytes`);
        }

        console.log('   Sending request...');
        const response = await fetch(url, options);

        console.log(`   Response status: ${response.status}`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`   Error: ${errorText}`);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const result = await response.json();
        console.log(`   ✅ Success!`);

        return result;
    }
}

// Register the Web Component
customElements.define('playground-controller', PlaygroundController);

console.log('✅ PlaygroundController component registered');