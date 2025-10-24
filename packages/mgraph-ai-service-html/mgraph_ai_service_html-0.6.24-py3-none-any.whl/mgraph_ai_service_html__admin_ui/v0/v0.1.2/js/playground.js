import { apiClient } from './services/API__Client.js';
import '../components/transformation-selector/Transformation__Selector.js';

console.log(">>> this shows in console")
document.addEventListener('DOMContentLoaded', () => {
    console.log(">>> this doesn't show in console")
    debugger
    const html_input              = document.getElementById('html-input');
    const transformation_selector = document.getElementById('transformation-selector');
    const output_viewer           = document.getElementById('output-viewer');

    let current_html = '';

    // Read initial HTML value from component (in case sample already loaded)
    const textarea = html_input.querySelector('textarea');
    if (textarea && textarea.value) {
        current_html = textarea.value;
        console.log('Initial HTML loaded:', current_html.length, 'characters');
    }

    // Listen for HTML changes from input component
    document.addEventListener('html-changed', (e) => {
        current_html = e.detail.html;
        console.log('HTML updated:', current_html.length, 'characters');
    });

    // Listen for transformation requests from selector component
    document.addEventListener('transformation-requested', async (e) => {
        const config = e.detail;
        console.log('Transformation requested:', config);

        // Validate input exists
        if (!current_html) {
            alert('Please enter or select HTML first!');
            return;
        }

        // Show loading state
        output_viewer.showLoading();

        try {
            // Build payload using API client helper
            const options = {};
            if (config.max_depth) {
                options.max_depth = config.max_depth;
            }

            let payload;
            try {
                payload = apiClient.build_payload(
                    config.endpoint_id,
                    current_html,
                    options
                );
            } catch (error) {
                // Handle special cases like hash operations not yet implemented
                if (config.input_type === 'hashes') {
                    alert('Hash operations require a dict and hash mapping. This workflow will be available in a future version. For now, try: HTML → Text Nodes to see hash mappings.');
                    output_viewer.showError(new Error('Hash operations not yet implemented in playground'));
                    return;
                }
                throw error;
            }

            // Call API using route from config
            console.log('Calling endpoint:', config.route, 'with payload:', payload);
            const result = await apiClient.call_endpoint(config.route, payload);
            console.log('Result received:', result);

            // Use output_type from config instead of detection logic
            const output_type = config.output_type || detect_output_type(result);

            // Show result in output viewer
            output_viewer.showResult(result, output_type);

        } catch (error) {
            console.error('Transformation failed:', error);
            output_viewer.showError(error);
        }
    });
});

/**
 * Fallback output type detection (used if config doesn't specify)
 */
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