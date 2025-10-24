/**
 * API Client Service - v0.1.2 Refactored
 * Simplified HTTP client that uses Endpoints__Config as single source of truth
 * Handles communication with HTML transformation service endpoints
 */

import { Endpoints__Config, Endpoints__Utils } from '../config/Endpoints__Config.js';

export class API__Client {
    constructor() {
        this.base_url = window.location.origin;                                // Same server, no CORS issues
    }

    /**
     * Generic endpoint caller - Core HTTP communication method
     */
    async call_endpoint(endpoint_route, payload) {
        const endpoint_config = this._find_endpoint_by_route(endpoint_route);  // Get metadata for better error context

        try {
            const response = await fetch(endpoint_route, {
                method : 'POST'                                                 ,
                headers: { 'Content-Type': 'application/json' }                ,
                body   : JSON.stringify(payload)
            });

            if (!response.ok) {
                const error_text = await response.text();
                const endpoint_name = endpoint_config ? endpoint_config.display_name : endpoint_route;
                throw new Error(`API Error [${endpoint_name}] ${response.status}: ${error_text}`);
            }

            return await response.json();

        } catch (error) {
            // Add endpoint context to error if not already present
            if (endpoint_config && !error.message.includes(endpoint_config.display_name)) {
                error.message = `[${endpoint_config.display_name}] ${error.message}`;
            }
            throw error;
        }
    }

    /**
     * Build payload based on endpoint configuration
     */
    build_payload(endpoint_id, input_data, options = {}) {
        const endpoint = Endpoints__Utils.get_endpoint(endpoint_id);

        if (!endpoint) {
            throw new Error(`Unknown endpoint: ${endpoint_id}`);
        }

        const payload = {};

        // Add input based on endpoint's input_type
        if (endpoint.input_type === 'html') {
            payload.html = input_data;
        }
        else if (endpoint.input_type === 'dict') {
            // Parse if string, otherwise use as-is
            payload.html_dict = typeof input_data === 'string'
                ? JSON.parse(input_data)
                : input_data;
        }
        else if (endpoint.input_type === 'hashes') {
            // Hash operations need both dict and mapping
            if (!options.html_dict || !options.hash_mapping) {
                throw new Error('Hash operations require both html_dict and hash_mapping');
            }
            payload.html_dict    = options.html_dict;
            payload.hash_mapping = options.hash_mapping;
        }

        // Add max_depth if provided in options
        if (options.max_depth !== undefined) {
            payload.max_depth = options.max_depth;
        }

        return payload;
    }

    /**
     * Call endpoint by ID with automatic payload construction
     */
    async call_by_id(endpoint_id, input_data, options = {}) {
        const endpoint = Endpoints__Utils.get_endpoint(endpoint_id);

        if (!endpoint) {
            throw new Error(`Unknown endpoint: ${endpoint_id}`);
        }

        const payload = this.build_payload(endpoint_id, input_data, options);
        return await this.call_endpoint(endpoint.route, payload);
    }

    /**
     * Get endpoint metadata by route (for error context)
     */
    _find_endpoint_by_route(route) {
        return Object.values(Endpoints__Config || {})
            .find(endpoint => endpoint.route === route);
    }
}



export const apiClient = new API__Client();