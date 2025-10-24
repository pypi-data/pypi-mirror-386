/**
 * Transformation Selector Component - v0.1.2 Refactored
 * UI component for selecting and configuring API endpoint transformations
 * Now uses Endpoints__Config as single source of truth
 */

import { Endpoints__Utils } from '../../js/config/Endpoints__Config.js';


export class Transformation__Selector extends HTMLElement {
    constructor() {
        super();
        this.template_url = '../v0.1.1/components/transformation-selector/transformation-selector.html';
        this.style_url    = '../v0.1.1/components/transformation-selector/transformation-selector.css';
    }

    async connectedCallback() {
        await this.load_styles();
        await this.load_template();
        this.populate_endpoint_selector();                                      // NEW: Auto-populate from config
        this.attach_event_listeners();
    }

    async load_styles() {
        const link = document.createElement('link');
        link.rel  = 'stylesheet';
        link.href = this.style_url;
        document.head.appendChild(link);
    }

    async load_template() {
        const response = await fetch(this.template_url);
        const html     = await response.text();
        this.innerHTML = html;
    }

    /**
     * Populate endpoint dropdown from Endpoints__Utils
     */
    populate_endpoint_selector() {
        const selector       = this.querySelector('#endpoint-selector');
        const grouped        = Endpoints__Utils.get_grouped_by_category();
        const category_names = {
            html   : 'HTML Transformations'  ,
            dict   : 'Dict Transformations'  ,
            hashes : 'Hash Transformations'
        };

        selector.innerHTML = '<option value="">-- Select Transformation --</option>';


        // Add grouped options
        Object.keys(category_names).forEach(category => {
            if (grouped[category] && grouped[category].length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = category_names[category];

                grouped[category].forEach(endpoint => {
                    const option  = document.createElement('option');
                    option.value  = endpoint.id;
                    option.text   = endpoint.display_name;
                    optgroup.appendChild(option);
                });

                selector.appendChild(optgroup);
            }
        });
    }

    attach_event_listeners() {
        const selector        = this.querySelector('#endpoint-selector');
        const transform_btn   = this.querySelector('#transform-btn');
        const max_depth_slider = this.querySelector('#max-depth-slider');
        const max_depth_value  = this.querySelector('#max-depth-value');

        // Endpoint selection
        selector.addEventListener('change', (e) => {
            const endpoint_id = e.target.value;
            if (endpoint_id) {
                this.show_endpoint_info(endpoint_id);
                transform_btn.disabled = false;
            } else {
                this.hide_endpoint_info();
                transform_btn.disabled = true;
            }
        });

        // Max depth slider
        max_depth_slider.addEventListener('input', (e) => {
            max_depth_value.textContent = e.target.value;
        });

        // Transform button
        transform_btn.addEventListener('click', () => {
            this.handle_transform();
        });
    }

    show_endpoint_info(endpoint_id) {
        const endpoint     = Endpoints__Utils.get_endpoint(endpoint_id);
        const info_div     = this.querySelector('#endpoint-info');
        const desc_span    = this.querySelector('#endpoint-description');
        const config_panel = this.querySelector('#config-panel');

        desc_span.textContent   = endpoint.description;
        info_div.style.display  = 'block';

        // Show config panel if max_depth is required
        if (endpoint.requires_max_depth) {
            config_panel.style.display = 'block';
        } else {
            config_panel.style.display = 'none';
        }
    }

    hide_endpoint_info() {
        const info_div     = this.querySelector('#endpoint-info');
        const config_panel = this.querySelector('#config-panel');

        info_div.style.display     = 'none';
        config_panel.style.display = 'none';
    }

    handle_transform() {
        //debugger
        const selector    = this.querySelector('#endpoint-selector');
        const endpoint_id = selector.value;
        const endpoint    = Endpoints__Utils.get_endpoint(endpoint_id);

        const config = {
            endpoint_id : endpoint_id      ,
            route       : endpoint.route   ,
            input_type  : endpoint.input_type,
            output_type : endpoint.output_type                                  // NEW: Include output type from config
        };

        // Add max_depth if required by endpoint
        if (endpoint.requires_max_depth) {
            const max_depth_slider = this.querySelector('#max-depth-slider');
            config.max_depth = parseInt(max_depth_slider.value);
        }

        this.emit('transformation-requested', config);
    }

    emit(event_name, detail) {
        this.dispatchEvent(new CustomEvent(event_name, {
            detail  : detail,
            bubbles : true
        }));
    }
}

customElements.define('transformation-selector', Transformation__Selector);