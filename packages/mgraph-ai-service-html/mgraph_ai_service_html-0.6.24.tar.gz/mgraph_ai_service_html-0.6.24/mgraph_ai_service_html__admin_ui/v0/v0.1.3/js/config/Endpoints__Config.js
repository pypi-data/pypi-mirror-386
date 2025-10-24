const response = await fetch('../v0.1.3/js/config/endpoints.json');

export const Endpoints__Config = await response.json();

// Utility functions for working with endpoints
export const Endpoints__Utils = {
    // Get endpoint by ID
    get_endpoint(endpoint_id) {
        return Endpoints__Config[endpoint_id];
    },

    // Get all endpoints in a category
    get_by_category(category) {
        return Object.values(Endpoints__Config)
            .filter(endpoint => endpoint.category === category);
    },

    // Get all endpoint IDs
    get_all_ids() {
        return Object.keys(Endpoints__Config);
    },

    // Get endpoints grouped by category
    get_grouped_by_category() {
        const grouped = {};
        Object.values(Endpoints__Config).forEach(endpoint => {
            if (!grouped[endpoint.category]) {
                grouped[endpoint.category] = [];
            }
            grouped[endpoint.category].push(endpoint);
        });
        return grouped;
    },

    // Validate if endpoint exists
    endpoint_exists(endpoint_id) {
        return endpoint_id in Endpoints__Config;
    }
};

