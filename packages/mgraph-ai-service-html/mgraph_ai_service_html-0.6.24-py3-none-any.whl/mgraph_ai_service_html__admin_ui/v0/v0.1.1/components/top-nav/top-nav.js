/**
 * Top Navigation Component
 * Displays navigation bar with active page highlighting
 */
class TopNav extends HTMLElement {
    constructor() {
        super();
        this.templateURL = '../v0.1.1/components/top-nav/top-nav.html';
        this.styleURL    = '../v0.1.1/components/top-nav/top-nav.css';
    }

    async connectedCallback() {
        await this.loadStyles();
        await this.loadTemplate();
        this.setActivePage();
    }

    async loadStyles() {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = this.styleURL;
        document.head.appendChild(link);
    }

    async loadTemplate() {
        const response = await fetch(this.templateURL);
        const html = await response.text();
        this.innerHTML = html;
    }

    setActivePage() {
        const currentPage = this.getAttribute('current-page');
        const links = this.querySelectorAll('.nav-links a');
        links.forEach(link => {
            if (link.getAttribute('data-page') === currentPage) {
                link.classList.add('active');
            }
        });
    }
}

customElements.define('top-nav', TopNav);
