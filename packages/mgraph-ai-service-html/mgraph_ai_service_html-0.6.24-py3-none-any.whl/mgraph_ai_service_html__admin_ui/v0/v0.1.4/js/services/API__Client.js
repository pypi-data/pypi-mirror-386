/**
 * API Client Service - v0.1.4 FIXED
 *
 * CRITICAL FIX: Only overrides call_endpoint() method to respect output_type
 *
 * Strategy: Import v0.1.2 API Client and extend it with minimal changes
 * - Inherits all other methods unchanged
 * - Only fixes the response parsing logic
 */

import { API__Client as API__Client__v0_1_2 } from '../../../v0.1.2/js/services/API__Client.js';

export class API__Client extends API__Client__v0_1_2 {
    /**
     * Override: Generic endpoint caller with FIXED response parsing
     *
     * ONLY CHANGE: Check output_type before parsing response
     * Everything else inherited from v0.1.2
     */
    async call_endpoint(endpoint_route, payload) {
        const endpoint_config = this._find_endpoint_by_route(endpoint_route);

        try {
            const response = await fetch(endpoint_route, {
                method : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body   : JSON.stringify(payload)
            });

            if (!response.ok) {
                const error_text = await response.text();
                const endpoint_name = endpoint_config ? endpoint_config.display_name : endpoint_route;
                throw new Error(`API Error [${endpoint_name}] ${response.status}: ${error_text}`);
            }

            // FIXED: Check output_type to determine how to parse response
            if (endpoint_config && endpoint_config.output_type) {
                if (endpoint_config.output_type === 'json') {
                    return await response.json();  // ✅ Parse as JSON only for JSON endpoints
                } else {
                    return await response.text();  // ✅ Return raw text for text/html endpoints
                }
            } else {
                // Fallback: try JSON first, fall back to text if it fails
                const text = await response.text();
                try {
                    return JSON.parse(text);
                } catch (e) {
                    return text;
                }
            }

        } catch (error) {
            // Add endpoint context to error if not already present
            if (endpoint_config && !error.message.includes(endpoint_config.display_name)) {
                error.message = `[${endpoint_config.display_name}] ${error.message}`;
            }
            throw error;
        }
    }

    // Note: All other methods inherited from v0.1.2:
    // - build_payload()
    // - call_by_id()
    // - _find_endpoint_by_route()
}

// Export singleton instance
export const apiClient = new API__Client();