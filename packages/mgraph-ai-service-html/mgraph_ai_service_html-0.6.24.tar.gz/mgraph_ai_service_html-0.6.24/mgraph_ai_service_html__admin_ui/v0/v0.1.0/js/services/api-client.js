/**
 * HTML Service API Client
 * v0.1.0
 * 
 * Service for communicating with HTML transformation API endpoints.
 * Handles all HTTP requests, error handling, and response parsing.
 */

class ApiClient {
    constructor() {
        // Base URL is same origin (no CORS issues)
        this.baseUrl = '';
        
        // Available endpoints configuration
        this.endpoints = {
            // HTML Routes
            html: {
                toDict: {
                    path: '/html/to__dict',
                    method: 'POST',
                    description: 'Parse HTML to dictionary structure'
                },
                toHtml: {
                    path: '/html/to__html',
                    method: 'POST',
                    description: 'Round-trip validation (HTML → Dict → HTML)'
                },
                toTextNodes: {
                    path: '/html/to__text__nodes',
                    method: 'POST',
                    description: 'Extract text nodes with hash identifiers'
                },
                toLines: {
                    path: '/html/to__lines',
                    method: 'POST',
                    description: 'Format HTML as readable lines'
                },
                toHtmlHashes: {
                    path: '/html/to__html__hashes',
                    method: 'POST',
                    description: 'Replace text with hashes (debugging)'
                },
                toHtmlXxx: {
                    path: '/html/to__html__xxx',
                    method: 'POST',
                    description: 'Replace text with x\'s (privacy masking)'
                }
            },
            // Dict Routes
            dict: {
                toHtml: {
                    path: '/dict/to__html',
                    method: 'POST',
                    description: 'Reconstruct HTML from dictionary'
                },
                toTextNodes: {
                    path: '/dict/to__text__nodes',
                    method: 'POST',
                    description: 'Extract text nodes from dictionary'
                },
                toLines: {
                    path: '/dict/to__lines',
                    method: 'POST',
                    description: 'Format dictionary as lines'
                }
            },
            // Hashes Routes
            hashes: {
                toHtml: {
                    path: '/hashes/to__html',
                    method: 'POST',
                    description: 'Apply hash mapping to reconstruct modified HTML'
                }
            }
        };
    }
    
    /**
     * Make API call to specified endpoint
     * @param {string} route - Full endpoint path (e.g., '/html/to__dict')
     * @param {object} payload - Request payload
     * @returns {Promise<{result: any, outputType: string}>}
     */
    async callEndpoint(route, payload) {
        try {
            const response = await fetch(route, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            
            // Check if response is OK
            if (!response.ok) {
                // Try to parse error message from API
                let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.detail || errorMsg;
                } catch {
                    // If can't parse JSON, use status text
                }
                throw new Error(errorMsg);
            }
            
            // Determine response type from Content-Type header
            const contentType = response.headers.get('content-type') || '';
            let result, outputType;
            
            if (contentType.includes('application/json')) {
                result = await response.json();
                outputType = 'json';
            } else if (contentType.includes('text/html')) {
                result = await response.text();
                outputType = 'html';
            } else if (contentType.includes('text/plain')) {
                result = await response.text();
                outputType = 'text';
            } else {
                // Default to text
                result = await response.text();
                outputType = 'text';
            }
            
            return { result, outputType };
            
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
    
    /**
     * Get endpoint information
     * @param {string} category - 'html', 'dict', or 'hashes'
     * @param {string} action - Specific action (e.g., 'toDict')
     * @returns {object|null} Endpoint configuration
     */
    getEndpointInfo(category, action) {
        return this.endpoints[category]?.[action] || null;
    }
    
    /**
     * Get all endpoints grouped by category
     * @returns {object} All endpoints configuration
     */
    getAllEndpoints() {
        return this.endpoints;
    }
    
    /**
     * Load sample HTML file
     * @param {string} samplePath - Path to sample file relative to /html-service/
     * @returns {Promise<string>} Sample HTML content
     */
    async loadSample(samplePath) {
        try {
            const response = await fetch(samplePath);
            
            if (!response.ok) {
                throw new Error(`Failed to load sample: ${response.statusText}`);
            }
            
            return await response.text();
        } catch (error) {
            console.error('Failed to load sample:', error);
            throw error;
        }
    }
    
    /**
     * Measure transformation performance
     * @param {string} route - Endpoint path
     * @param {object} payload - Request payload
     * @returns {Promise<{result: any, outputType: string, duration: number, size: number}>}
     */
    async callWithMetrics(route, payload) {
        const startTime = performance.now();
        
        const { result, outputType } = await this.callEndpoint(route, payload);
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        // Calculate result size
        const resultString = typeof result === 'object' ? JSON.stringify(result) : result;
        const size = new Blob([resultString]).size;
        
        return {
            result,
            outputType,
            duration: Math.round(duration),
            size
        };
    }
    
    /**
     * Format bytes to human readable size
     * @param {number} bytes - Size in bytes
     * @returns {string} Formatted size (e.g., "1.5 KB")
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// Create global instance
window.apiClient = new ApiClient();

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
}
