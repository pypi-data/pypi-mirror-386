import { apiClient } from '../../v0.1.4/js/services/API__Client.js';
import '../../v0.1.2/components/transformation-selector/Transformation__Selector.js';

/**
 * Playground Initialization - v0.1.4
 *
 * FIXED: Removed detect_output_type() function
 * Now uses output_type directly from endpoint configuration
 */

// Function to initialize
function init() {

    const html_input              = document.getElementById('html-input');
    const transformation_selector = document.getElementById('transformation-selector');
    const output_viewer           = document.getElementById('output-viewer');

    let current_html = '';

    // Read initial HTML value
    const textarea = html_input.querySelector('textarea');
    if (textarea && textarea.value) {
        current_html = textarea.value;
    }

    // Listen for HTML changes
    document.addEventListener('html-changed', (e) => {
        current_html = e.detail.html;
        console.log('HTML updated:', current_html.length, 'characters');
    });

    // Listen for transformation requests
    document.addEventListener('transformation-requested', async (e) => {
        const config = e.detail;
        //console.log('Transformation requested:', config);

        if (!current_html) {
            alert('Please enter or select HTML first!');
            return;
        }

        output_viewer.showLoading();

        try {
            const options = {};
            if (config.max_depth) {
                options.max_depth = config.max_depth;
            }

            const payload = apiClient.build_payload(
                config.endpoint_id,
                current_html,
                options
            );

            //console.log('Calling endpoint:', config.route, 'with payload:', payload);
            const result = await apiClient.call_endpoint(config.route, payload);
            //console.log('Result received:', result);

            // FIXED: Use output_type from endpoint config directly
            // No need to detect - the config already tells us the type!
            const output_type = config.output_type || 'text';
            //console.log('Using output_type from config:', output_type);

            output_viewer.showResult(result, output_type);

        } catch (error) {
            console.error('Transformation failed:', error);
            output_viewer.showError(error);
        }
    });
}

// Check if DOM is already ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    // DOM already loaded, execute immediately
    init();
}