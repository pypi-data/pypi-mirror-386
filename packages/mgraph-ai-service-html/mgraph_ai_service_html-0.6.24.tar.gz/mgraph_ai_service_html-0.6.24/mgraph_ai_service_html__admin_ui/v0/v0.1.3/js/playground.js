import { apiClient } from '../../v0.1.2/js/services/API__Client.js';
import '../../v0.1.2/components/transformation-selector/Transformation__Selector.js';



// Function to initialize
function init() {
    console.log(">>> Initializing playground");

    const html_input              = document.getElementById('html-input');
    const transformation_selector = document.getElementById('transformation-selector');
    const output_viewer           = document.getElementById('output-viewer');

    let current_html = '';

    // Read initial HTML value
    const textarea = html_input.querySelector('textarea');
    if (textarea && textarea.value) {
        current_html = textarea.value;
        console.log('Initial HTML loaded:', current_html.length, 'characters');
    }

    // Listen for HTML changes
    document.addEventListener('html-changed', (e) => {
        current_html = e.detail.html;
        console.log('HTML updated:', current_html.length, 'characters');
    });

    // Listen for transformation requests
    document.addEventListener('transformation-requested', async (e) => {
        const config = e.detail;
        console.log('Transformation requested:', config);

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

            console.log('Calling endpoint:', config.route, 'with payload:', payload);
            const result = await apiClient.call_endpoint(config.route, payload);
            console.log('Result received:', result);

            const output_type = config.output_type || detect_output_type(result);
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

function detect_output_type(result) {
    if (typeof result === 'object') {
        return 'json';
    }
    else if (typeof result === 'string') {
        if (result.trim().startsWith('<')) {
            return 'html';
        }
        return 'text';
    }
    return 'text';
}