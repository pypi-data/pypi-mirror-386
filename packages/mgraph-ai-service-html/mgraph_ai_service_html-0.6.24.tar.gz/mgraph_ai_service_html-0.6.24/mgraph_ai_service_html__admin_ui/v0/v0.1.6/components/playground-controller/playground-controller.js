/**
 * Playground Controller - v0.1.6 (Refactored)
 * Orchestrator component - coordinates state and API calls
 * NO DOM manipulation - components manage their own DOM
 *
 * Event-driven architecture:
 * - Listens to events from column components
 * - Makes API calls
 * - Dispatches results back to components
 */

import { Syntax__Highlighter } from '../../../v0.1.4/js/utils/Syntax__Highlighter.js';

class PlaygroundController extends HTMLElement {
    constructor() {
        super();
        console.log('🎮 PlaygroundController constructor (v0.1.6 Refactored)');

        // State management only - no DOM references
        this.state = {
            originalHtml: '',
            currentDict: null,
            currentHashes: null,
            currentCreatedHtml: ''
        };

        // Load syntax highlighter styles
        Syntax__Highlighter.loadStyles();
    }

    connectedCallback() {
        console.log('🎮 PlaygroundController connected - setting up event listeners');
        this.setupEventListeners();

        // Auto-run full flow on load
        // setTimeout(() => {
        //     this.runFullFlow();
        // }, 500);
    }

    disconnectedCallback() {
        console.log('🎮 PlaygroundController disconnected');
    }

    /**
     * Setup event listeners for all component events
     */
    setupEventListeners() {
        // Listen to HTML changes from column-original
        document.addEventListener('html-changed', (e) => {
            this.state.originalHtml = e.detail.html;
            console.log(`🎮 HTML changed: ${e.detail.html.length} characters`);
        });

        // Listen to parse requests from column-middle
        document.addEventListener('parse-requested', () => {
            console.log('🎮 Parse requested');
            this.handleParse();
        });

        // Listen to rebuild requests from column-created
        document.addEventListener('rebuild-requested', () => {
            console.log('🎮 Rebuild requested');
            this.handleRebuild();
        });

        // Listen to copy requests from column-created
        document.addEventListener('copy-requested', () => {
            console.log('🎮 Copy requested');
            this.handleCopy();
        });

        // Listen to download requests from column-created
        document.addEventListener('download-requested', () => {
            console.log('🎮 Download requested');
            this.handleDownload();
        });

        // Listen to debug panel actions
        document.addEventListener('debug-action', (e) => {
            console.log(`🎮 Debug action: ${e.detail.action}`);
            this.handleDebugAction(e.detail.action);
        });

        console.log('✅ All event listeners attached');
    }

    /**
     * Handle parse HTML → Dict + Hashes
     */
    async handleParse() {
        const html = this.state.originalHtml.trim();

        if (!html) {
            this.showStatus('error', 'Please enter some HTML to parse');
            return;
        }

        this.showStatus('loading', 'Parsing HTML...');

        try {
            const url = '/html/to/dict/hashes';
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ html: html, max_depth: 256 })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();

            // Update state
            this.state.currentDict = result.html_dict;
            this.state.currentHashes = result.hash_mapping;

            // Send data to column-middle
            const columnMiddle = document.querySelector('column-middle');
            if (columnMiddle) {
                columnMiddle.setData(result.html_dict, result.hash_mapping);
            }

            this.showStatus('success', 'HTML parsed successfully!');
            console.log('✅ Parse complete');

        } catch (error) {
            this.showStatus('error', `Parse failed: ${error.message}`);
            console.error('❌ Parse error:', error);
        }
    }

    /**
     * Handle rebuild HTML from Dict + Hashes
     */
    async handleRebuild() {
        // Get data from column-middle (in case it was edited)
        const columnMiddle = document.querySelector('column-middle');
        if (columnMiddle) {
            const data = columnMiddle.getData();
            this.state.currentDict = data.dict;
            this.state.currentHashes = data.hashes;
        }

        if (!this.state.currentDict || !this.state.currentHashes) {
            this.showStatus('error', 'Please parse HTML first');
            return;
        }

        this.showStatus('loading', 'Rebuilding HTML...');

        try {
            const url = '/hashes/to/html';
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    html_dict: this.state.currentDict,
                    hash_mapping: this.state.currentHashes
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const htmlResult = await response.text();

            // Update state
            this.state.currentCreatedHtml = htmlResult;

            // Send to column-created
            const columnCreated = document.querySelector('column-created');
            if (columnCreated) {
                columnCreated.setHtml(htmlResult);
            }

            this.showStatus('success', 'HTML rebuilt successfully!');
            console.log('✅ Rebuild complete');

        } catch (error) {
            this.showStatus('error', `Rebuild failed: ${error.message}`);
            console.error('❌ Rebuild error:', error);
        }
    }

    /**
     * Handle copy to clipboard
     */
    async handleCopy() {
        if (!this.state.currentCreatedHtml) {
            this.showStatus('error', 'No output to copy');
            return;
        }

        try {
            if (!navigator.clipboard) {
                throw new Error('Clipboard API not available');
            }

            await navigator.clipboard.writeText(this.state.currentCreatedHtml);
            this.showStatus('success', 'Copied to clipboard!');
            console.log('✅ Copied successfully');
        } catch (error) {
            this.showStatus('error', `Copy failed: ${error.message}`);
            console.error('❌ Copy error:', error);
        }
    }

    /**
     * Handle download as file
     */
    handleDownload() {
        if (!this.state.currentCreatedHtml) {
            this.showStatus('error', 'No output to download');
            return;
        }

        const blob = new Blob([this.state.currentCreatedHtml], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'reconstructed.html';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showStatus('success', 'Download started!');
        console.log('✅ Download started');
    }

    /**
     * Handle debug panel actions
     */
    async handleDebugAction(action) {
        const columnOriginal = document.querySelector('column-original');

        switch (action) {
            case 'load-micro':
                if (columnOriginal) {
                    columnOriginal.loadSample('micro');
                }
                break;

            case 'load-simple':
                if (columnOriginal) {
                    columnOriginal.loadSample('simple');
                }
                break;

            case 'parse':
                await this.handleParse();
                break;

            case 'rebuild':
                await this.handleRebuild();
                break;

            case 'full-flow':
                await this.runFullFlow();
                break;
        }
    }

    /**
     * Run full flow: Load → Parse → Rebuild
     */
    async runFullFlow() {
        console.log('⚡ Starting full flow...');

        // Load micro sample
        const columnOriginal = document.querySelector('column-original');
        if (columnOriginal) {
            columnOriginal.loadSample('micro');
        }

        await this.delay(300);

        // Parse
        await this.handleParse();
        await this.delay(300);

        // Rebuild
        await this.handleRebuild();

        console.log('✅ Full flow complete!');
    }

    /**
     * Show status message (in header)
     */
    showStatus(type, message) {
        const statusEl = document.getElementById('status-message');
        if (!statusEl) return;

        statusEl.textContent = message;
        statusEl.className = `status-message status-${type}`;
        statusEl.style.display = 'block';

        // Auto-dismiss after 4 seconds for success
        if (type === 'success') {
            setTimeout(() => {
                statusEl.style.display = 'none';
            }, 4000);
        }
    }

    /**
     * Helper: delay
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

customElements.define('playground-controller', PlaygroundController);
console.log('✅ PlaygroundController component registered (v0.1.6 Refactored)');
