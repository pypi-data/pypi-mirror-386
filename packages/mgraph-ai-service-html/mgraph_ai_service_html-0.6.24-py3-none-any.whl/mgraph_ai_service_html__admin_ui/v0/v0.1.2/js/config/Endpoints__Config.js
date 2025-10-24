/**
 * Endpoints Configuration
 * Single source of truth for all HTML transformation API endpoints
 * Version: v0.1.2
 */

export const Endpoints__Config = {
    // HTML Transformations
    'html-to-dict': {
        id              : 'html-to-dict'                                        ,
        display_name    : 'HTML → Dict'                                         ,
        route           : '/html/to/dict'                                       ,
        method          : 'POST'                                                ,
        description     : 'Parse HTML into a nested dictionary structure representing the DOM tree',
        category        : 'html'                                                ,
        input_type      : 'html'                                                ,
        output_type     : 'json'                                                ,
        requires_max_depth: false                                               ,
        parameters      : {
            html       : { required: true , type: 'string'  }                   ,
            max_depth  : { required: false, type: 'integer', default: 256 }
        }
    },

    'html-to-text-nodes': {
        id              : 'html-to-text-nodes'                                  ,
        display_name    : 'HTML → Text Nodes'                                   ,
        route           : '/html/to/text/nodes'                                 ,
        method          : 'POST'                                                ,
        description     : 'Extract all text nodes with unique hash identifiers for semantic modification',
        category        : 'html'                                                ,
        input_type      : 'html'                                                ,
        output_type     : 'json'                                                ,
        requires_max_depth: true                                                ,
        parameters      : {
            html       : { required: true , type: 'string'  }                   ,
            max_depth  : { required: true , type: 'integer', default: 256 }
        }
    },

    'html-to-tree-view': {
        id              : 'html-to-tree-view'                                   ,
        display_name    : 'HTML → Tree View'                                    ,
        route           : '/html/to/tree/view'                                  ,
        method          : 'POST'                                                ,
        description     : 'Format HTML as readable indented tree view showing structure',
        category        : 'html'                                                ,
        input_type      : 'html'                                                ,
        output_type     : 'text'                                                ,
        requires_max_depth: false                                               ,
        parameters      : {
            html       : { required: true , type: 'string'  }                   ,
            max_depth  : { required: false, type: 'integer', default: 256 }
        }
    },

    'html-to-html-hashes': {
        id              : 'html-to-html-hashes'                                 ,
        display_name    : 'HTML → HTML (Hashes)'                                ,
        route           : '/html/to/html/hashes'                                ,
        method          : 'POST'                                                ,
        description     : 'Replace all text content with hash identifiers (debugging visualization)',
        category        : 'html'                                                ,
        input_type      : 'html'                                                ,
        output_type     : 'html'                                                ,
        requires_max_depth: true                                                ,
        parameters      : {
            html       : { required: true , type: 'string'  }                   ,
            max_depth  : { required: true , type: 'integer', default: 256 }
        }
    },

    'html-to-html-xxx': {
        id              : 'html-to-html-xxx'                                    ,
        display_name    : 'HTML → HTML (XXX)'                                   ,
        route           : '/html/to/html/xxx'                                   ,
        method          : 'POST'                                                ,
        description     : 'Replace all text content with x\'s (privacy masking visualization)',
        category        : 'html'                                                ,
        input_type      : 'html'                                                ,
        output_type     : 'html'                                                ,
        requires_max_depth: true                                                ,
        parameters      : {
            html       : { required: true , type: 'string'  }                   ,
            max_depth  : { required: true , type: 'integer', default: 256 }
        }
    },

    // Dict Transformations
    'dict-to-html': {
        id              : 'dict-to-html'                                        ,
        display_name    : 'Dict → HTML'                                         ,
        route           : '/dict/to/html'                                       ,
        method          : 'POST'                                                ,
        description     : 'Reconstruct HTML from dictionary structure'          ,
        category        : 'dict'                                                ,
        input_type      : 'dict'                                                ,
        output_type     : 'html'                                                ,
        requires_max_depth: false                                               ,
        parameters      : {
            html_dict  : { required: true , type: 'object' }                    ,
            max_depth  : { required: false, type: 'integer', default: 256 }
        }
    },

    'dict-to-text-nodes': {
        id              : 'dict-to-text-nodes'                                  ,
        display_name    : 'Dict → Text Nodes'                                   ,
        route           : '/dict/to/text/nodes'                                 ,
        method          : 'POST'                                                ,
        description     : 'Extract text nodes from dictionary structure'        ,
        category        : 'dict'                                                ,
        input_type      : 'dict'                                                ,
        output_type     : 'json'                                                ,
        requires_max_depth: true                                                ,
        parameters      : {
            html_dict  : { required: true , type: 'object' }                    ,
            max_depth  : { required: true , type: 'integer', default: 256 }
        }
    },

    'dict-to-tree-view': {
        id              : 'dict-to-tree-view'                                   ,
        display_name    : 'Dict → Tree View'                                    ,
        route           : '/dict/to/tree/view'                                  ,
        method          : 'POST'                                                ,
        description     : 'Format dictionary as readable tree view'             ,
        category        : 'dict'                                                ,
        input_type      : 'dict'                                                ,
        output_type     : 'text'                                                ,
        requires_max_depth: false                                               ,
        parameters      : {
            html_dict  : { required: true , type: 'object' }                    ,
            max_depth  : { required: false, type: 'integer', default: 256 }
        }
    },

    // Hash Transformations
    'hashes-to-html': {
        id              : 'hashes-to-html'                                      ,
        display_name    : 'Hashes → HTML'                                       ,
        route           : '/hashes/to/html'                                     ,
        method          : 'POST'                                                ,
        description     : 'Apply hash mappings to reconstruct HTML with modified text',
        category        : 'hashes'                                              ,
        input_type      : 'hashes'                                              ,
        output_type     : 'html'                                                ,
        requires_max_depth: false                                               ,
        parameters      : {
            html_dict    : { required: true , type: 'object' }                  ,
            hash_mapping : { required: true , type: 'object' }                  ,
            max_depth    : { required: false, type: 'integer', default: 256 }
        }
    }
};

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

