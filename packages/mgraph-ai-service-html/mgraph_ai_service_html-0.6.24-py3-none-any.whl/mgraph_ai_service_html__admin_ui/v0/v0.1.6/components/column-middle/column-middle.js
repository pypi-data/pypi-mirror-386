/**
 * Column Middle Component - v0.1.6 (Refactored)
 * Orchestrates: column-header, json-view-mode (x2), json-edit-mode (x2)
 *
 * Emits:
 *   parse-requested - {}
 *   dict-changed - { dict: object }
 *   hashes-changed - { hashes: object }
 */

import { ComponentUtils } from '../../../v0.1.6/utils/ComponentUtils.js';

class ColumnMiddle extends HTMLElement {
    constructor() {
        super();
        console.log('🧩 ColumnMiddle constructor (refactored)');
        this.mode = 'view'; // 'view' | 'edit'
        this.templateLoaded = false;
    }

    async connectedCallback() {
        ComponentUtils.loadStyles(
            'column-middle-styles',
            '../v0.1.6/components/column-middle/column-middle.css'
        );

        this.templateLoaded = await ComponentUtils.loadTemplate(
            this,
            '../v0.1.6/components/column-middle/column-middle.html'
        );

        if (this.templateLoaded) {
            // Use setTimeout to ensure DOM is fully ready
            setTimeout(() => this.attachListeners(), 0);
        }
    }

    attachListeners() {
        // Parse button
        const parseBtn = ComponentUtils.$(this, '#btn-parse');

        if (parseBtn) {
            ComponentUtils.on(parseBtn, 'click', () => {
                console.log('🧩 ColumnMiddle: Parse button clicked');
                ComponentUtils.emitEvent(this, 'parse-requested');
            });
            console.log('🧩 ColumnMiddle: Parse button listener attached');
        } else {
            console.error('🧩 ColumnMiddle: Parse button not found!');
        }

        // Mode change listener
        this.addEventListener('mode-selected', (e) => {
            if (e.detail.columnId === 'middle') {
                this.switchMode(e.detail.mode);
            }
        });

        // Listen to JSON changes from edit mode
        this.addEventListener('json-changed', (e) => {
            const target = e.target;

            if (target.id === 'dict-edit' && e.detail.isValid) {
                ComponentUtils.emitEvent(this, 'dict-changed', {
                    dict: e.detail.json
                });
            } else if (target.id === 'hashes-edit' && e.detail.isValid) {
                ComponentUtils.emitEvent(this, 'hashes-changed', {
                    hashes: e.detail.json
                });
            }
        });

        console.log('🧩 ColumnMiddle: All listeners attached');
    }

    switchMode(mode) {
        console.log(`🧩 ColumnMiddle: Switching to ${mode} mode`);
        this.mode = mode;

        // Update column data-mode attribute
        const column = ComponentUtils.$(this, '.middle-column');
        column?.setAttribute('data-mode', mode);

        // Update header
        const header = ComponentUtils.$(this, 'column-header');
        header?.setAttribute('active-mode', mode);

        // Show/hide mode containers
        const viewContainer = ComponentUtils.$(this, '.mode-view');
        const editContainer = ComponentUtils.$(this, '.mode-edit');

        if (mode === 'view') {
            ComponentUtils.toggle(viewContainer, true);
            ComponentUtils.toggle(editContainer, false);

            // Sync from edit mode if switching back
            this.syncFromEdit();
        } else {
            ComponentUtils.toggle(viewContainer, false);
            ComponentUtils.toggle(editContainer, true);

            // Populate edit mode with current data
            this.populateEditMode();
        }
    }

    populateEditMode() {
        console.log('🧩 ColumnMiddle: Populating edit mode');

        const dictEdit = ComponentUtils.$(this, '#dict-edit');
        const hashesEdit = ComponentUtils.$(this, '#hashes-edit');

        const dictView = ComponentUtils.$(this, '#dict-view');
        const hashesView = ComponentUtils.$(this, '#hashes-view');

        if (dictEdit && dictView) {
            const dictData = dictView.getData();
            if (dictData) {
                dictEdit.setData(dictData);
            }
        }

        if (hashesEdit && hashesView) {
            const hashesData = hashesView.getData();
            if (hashesData) {
                hashesEdit.setData(hashesData);
            }
        }
    }

    syncFromEdit() {
        console.log('🧩 ColumnMiddle: Syncing from edit mode');

        const dictEdit = ComponentUtils.$(this, '#dict-edit');
        const hashesEdit = ComponentUtils.$(this, '#hashes-edit');

        const dictView = ComponentUtils.$(this, '#dict-view');
        const hashesView = ComponentUtils.$(this, '#hashes-view');

        if (dictEdit && dictView) {
            const dictData = dictEdit.getData();
            if (dictData) {
                dictView.setData(dictData);
            }
        }

        if (hashesEdit && hashesView) {
            const hashesData = hashesEdit.getData();
            if (hashesData) {
                hashesView.setData(hashesData);
            }
        }
    }

    // Public API
    setData(dict, hashes) {
        console.log('🧩 ColumnMiddle: Setting data', dict, hashes);

        const dictView = ComponentUtils.$(this, '#dict-view');
        const hashesView = ComponentUtils.$(this, '#hashes-view');

        if (dictView) {
            dictView.setData(dict);
        }

        if (hashesView) {
            hashesView.setData(hashes);
        }

        // If in edit mode, also update edit components
        if (this.mode === 'edit') {
            const dictEdit = ComponentUtils.$(this, '#dict-edit');
            const hashesEdit = ComponentUtils.$(this, '#hashes-edit');

            if (dictEdit) {
                dictEdit.setData(dict);
            }

            if (hashesEdit) {
                hashesEdit.setData(hashes);
            }
        }
    }

    getData() {
        // Always get from current mode
        if (this.mode === 'edit') {
            const dictEdit = ComponentUtils.$(this, '#dict-edit');
            const hashesEdit = ComponentUtils.$(this, '#hashes-edit');

            return {
                dict: dictEdit ? dictEdit.getData() : null,
                hashes: hashesEdit ? hashesEdit.getData() : null
            };
        } else {
            const dictView = ComponentUtils.$(this, '#dict-view');
            const hashesView = ComponentUtils.$(this, '#hashes-view');

            return {
                dict: dictView ? dictView.getData() : null,
                hashes: hashesView ? hashesView.getData() : null
            };
        }
    }
}

customElements.define('column-middle', ColumnMiddle);
console.log('✅ ColumnMiddle component registered (refactored)');