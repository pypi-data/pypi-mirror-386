/**
 * API Client Service for HTML Transformation Service
 * Handles all communication with service endpoints
 */
class APIClient {
    constructor() {
        this.baseURL = window.location.origin; // Same server, no CORS!
    }

    /**
     * Generic endpoint caller
     * @param {string} endpoint - API route (e.g., '/html/to__dict')
     * @param {object} payload - Request body
     * @returns {Promise<object>} - Response data
     */
    async callEndpoint(endpoint, payload) {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error ${response.status}: ${errorText}`);
        }

        return await response.json();
    }

    /**
     * Convenience methods for specific endpoints
     */
    
    // HTML transformations
    async htmlToDict(html) {
        return this.callEndpoint('/html/to__dict', { html });
    }

    async htmlToTextNodes(html, maxDepth = 256) {
        return this.callEndpoint('/html/to__text__nodes', { 
            html, 
            max_depth: maxDepth 
        });
    }

    async htmlToLines(html) {
        return this.callEndpoint('/html/to__lines', { html });
    }

    async htmlToHtmlHashes(html, maxDepth = 256) {
        return this.callEndpoint('/html/to__html__hashes', { 
            html, 
            max_depth: maxDepth 
        });
    }

    async htmlToHtmlXxx(html, maxDepth = 256) {
        return this.callEndpoint('/html/to__html__xxx', { 
            html, 
            max_depth: maxDepth 
        });
    }

    // Dict operations
    async dictToHtml(htmlDict) {
        return this.callEndpoint('/dict/to__html', { html_dict: htmlDict });
    }

    async dictToTextNodes(htmlDict, maxDepth = 256) {
        return this.callEndpoint('/dict/to__text__nodes', { 
            html_dict: htmlDict, 
            max_depth: maxDepth 
        });
    }

    async dictToLines(htmlDict) {
        return this.callEndpoint('/dict/to__lines', { html_dict: htmlDict });
    }

    // Hash operations
    async hashesToHtml(htmlDict, hashMapping) {
        return this.callEndpoint('/hashes/to__html', { 
            html_dict: htmlDict, 
            hash_mapping: hashMapping 
        });
    }

    /**
     * Event emitter for cross-component communication
     */
    emit(eventName, detail) {
        window.dispatchEvent(new CustomEvent(eventName, { detail }));
    }

    on(eventName, handler) {
        window.addEventListener(eventName, handler);
    }

    off(eventName, handler) {
        window.removeEventListener(eventName, handler);
    }
}

// Create global instance
window.apiClient = new APIClient();
