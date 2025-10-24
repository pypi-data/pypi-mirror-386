/**
 * Playground Page Orchestrator
 * Coordinates events between html-input, transformation-selector, and output-viewer
 */
document.addEventListener('DOMContentLoaded', () => {
    const htmlInput = document.getElementById('html-input');
    const transformationSelector = document.getElementById('transformation-selector');
    const outputViewer = document.getElementById('output-viewer');

    let currentHtml = '';

    // Listen for HTML changes
    document.addEventListener('html-changed', (e) => {
        currentHtml = e.detail.html;
        console.log('HTML updated:', currentHtml.length, 'characters');
    });

    // Listen for transformation requests
    document.addEventListener('transformation-requested', async (e) => {
        const config = e.detail;
        console.log('Transformation requested:', config);

        if (!currentHtml) {
            alert('Please enter or select HTML first!');
            return;
        }

        // Show loading
        outputViewer.showLoading();

        try {
            let result, outputType;

            // Build payload based on input type
            let payload = {};
            
            if (config.inputType === 'html') {
                payload.html = currentHtml;
            } else if (config.inputType === 'dict') {
                // Parse current HTML as JSON (assumes it's already a dict)
                try {
                    payload.html_dict = JSON.parse(currentHtml);
                } catch (error) {
                    throw new Error('Input must be valid JSON for dict operations. Try running HTML → Dict first, then use that output.');
                }
            } else if (config.inputType === 'hashes') {
                // For hash operations, need both dict and hash_mapping
                alert('Hash operations require a dict and hash mapping. This workflow will be available in a future version. For now, try: HTML → Text Nodes to see hash mappings.');
                outputViewer.showError(new Error('Hash operations not yet implemented in playground'));
                return;
            }

            // Add max_depth if provided
            if (config.maxDepth) {
                payload.max_depth = config.maxDepth;
            }

            // Call API
            console.log('Calling endpoint:', config.route, 'with payload:', payload);
            result = await window.apiClient.callEndpoint(config.route, payload);
            console.log('Result received:', result);

            // Determine output type
            if (typeof result === 'object') {
                outputType = 'json';
            } else if (typeof result === 'string') {
                // Check if it looks like HTML
                if (result.trim().startsWith('<')) {
                    outputType = 'html';
                } else {
                    outputType = 'text';
                }
            } else {
                outputType = 'text';
            }

            // Show result
            outputViewer.showResult(result, outputType);

        } catch (error) {
            console.error('Transformation failed:', error);
            outputViewer.showError(error);
        }
    });
});
