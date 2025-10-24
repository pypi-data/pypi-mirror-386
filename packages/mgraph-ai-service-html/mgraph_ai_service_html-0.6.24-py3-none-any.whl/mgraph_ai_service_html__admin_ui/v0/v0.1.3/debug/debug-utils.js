/**
 * Debug Utilities - Playground Testing Helpers
 * Add this script to playground.html for debugging features
 */

function addDebugButtons() {
    // Container for all debug buttons
    const container = document.createElement('div');
    container.id = 'debug-buttons-container';
    container.style.cssText = `
        position: fixed;
        top: 100px;
        right: 10px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 8px;
    `;

    // Define HTML transformations to test
    const htmlTransformations = [
        { id: 'html-to-dict'       , label: 'HTML→Dict'        , emoji: '📘' },
        { id: 'html-to-text-nodes' , label: 'HTML→Text Nodes'  , emoji: '📝' },
        { id: 'html-to-tree-view'  , label: 'HTML→Tree View'   , emoji: '🌳' },
        { id: 'html-to-html-hashes', label: 'HTML→HTML (Hash)' , emoji: '#️⃣' },
        { id: 'html-to-html-xxx'   , label: 'HTML→HTML (XXX)'  , emoji: '❌' }
    ];

    // Create a button for each transformation
    htmlTransformations.forEach(transform => {
        const btn = createDebugButton(transform);
        container.appendChild(btn);
    });

    // Add to page
    document.body.appendChild(container);
    //console.log('✅ Debug buttons added to page');
}

function createDebugButton(transform) {
    const btn = document.createElement('button');
    btn.className = 'debug-transform-btn';
    btn.innerHTML = `${transform.emoji} ${transform.label}`;

    // Gradient colors for each button type
    const gradients = {
        'html-to-dict'       : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'html-to-text-nodes' : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'html-to-tree-view'  : 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'html-to-html-hashes': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
        'html-to-html-xxx'   : 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
    };

    btn.style.cssText = `
        padding: 10px 15px;
        background: ${gradients[transform.id]};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 13px;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        min-width: 180px;
        text-align: left;
        white-space: nowrap;
    `;

    // Hover effects
    btn.addEventListener('mouseenter', () => {
        btn.style.transform = 'translateX(-5px)';
        btn.style.boxShadow = '0 6px 12px rgba(0,0,0,0.15)';
    });

    btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'translateX(0)';
        btn.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
    });

    // Click handler
    btn.addEventListener('click', () => {
        //console.log(`🐛 Debug: Simulating ${transform.label}`);
        simulateTransform(transform.id);
    });

    return btn;
}

function simulateTransform(endpointId) {
    //console.log(`🐛 Starting simulation for: ${endpointId}`);

    // 1. Get the dropdown selector
    const selector = document.querySelector('#endpoint-selector');

    if (!selector) {
        console.error('❌ Could not find #endpoint-selector');
        return;
    }

    // 2. Set the value to the specified endpoint
    selector.value = endpointId;

    // 3. Trigger the 'change' event to update the UI
    const changeEvent = new Event('change', { bubbles: true });
    selector.dispatchEvent(changeEvent);
    //console.log(`✅ Selected "${endpointId}"`);

    // 4. Wait a moment for UI to update, then click Transform
    setTimeout(() => {
        const transformBtn = document.querySelector('#transform-btn');

        if (!transformBtn) {
            console.error('❌ Could not find #transform-btn');
            return;
        }

        if (transformBtn.disabled) {
            console.warn('⚠️ Transform button is disabled');
            return;
        }

        transformBtn.click();
        //console.log('✅ Clicked Transform button');
    }, 100);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addDebugButtons);
} else {
    // DOM already loaded
    addDebugButtons();
}