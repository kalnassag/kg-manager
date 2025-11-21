/**
 * Language Selector Component
 *
 * Creates a dropdown for selecting the UI language.
 * Integrates with the i18n system and fetches available locales from the API.
 */

class LanguageSelector {
    constructor(containerId = 'language-selector') {
        this.containerId = containerId;
        this.locales = [];
        this.init();
    }

    /**
     * Initialize the language selector
     */
    async init() {
        // Wait for i18n to be ready
        if (!window.i18n) {
            console.error('i18n system not found');
            return;
        }

        // Fetch available locales from API
        await this.fetchLocales();

        // Create selector UI
        this.render();

        // Listen for locale changes
        window.addEventListener('localechanged', (e) => {
            this.updateSelected(e.detail.locale);
        });
    }

    /**
     * Fetch available locales from the API
     */
    async fetchLocales() {
        try {
            const response = await fetch('/api/locales');
            if (!response.ok) {
                throw new Error('Failed to fetch locales');
            }

            const data = await response.json();
            this.locales = data.locales;
            this.defaultLocale = data.default_locale;

            console.log(`Loaded ${this.locales.length} locales from API`);
        } catch (error) {
            console.error('Error fetching locales:', error);

            // Fallback to hardcoded locales
            this.locales = window.i18n.getAvailableLocales().map(code => ({
                code: code,
                name: window.i18n.getLocaleDisplayName(code),
                rtl: window.i18n.isRTL(code)
            }));
            this.defaultLocale = 'en';
        }
    }

    /**
     * Render the language selector
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container #${this.containerId} not found`);
            return;
        }

        const currentLocale = window.i18n.getLocale();

        // Create dropdown HTML
        const html = `
            <div class="language-selector">
                <button class="language-selector-btn" id="language-selector-btn" aria-label="Select language">
                    <svg class="language-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M10 1C14.97 1 19 5.03 19 10C19 14.97 14.97 19 10 19C5.03 19 1 14.97 1 10C1 5.03 5.03 1 10 1ZM10 2.5C5.86 2.5 2.5 5.86 2.5 10C2.5 14.14 5.86 17.5 10 17.5C14.14 17.5 17.5 14.14 17.5 10C17.5 5.86 14.14 2.5 10 2.5ZM10 4C11.33 5.67 12.12 7.74 12.12 10C12.12 12.26 11.33 14.33 10 16C8.67 14.33 7.88 12.26 7.88 10C7.88 7.74 8.67 5.67 10 4ZM4.26 8H6.54C6.77 6.5 7.26 5.1 7.93 3.86C6.27 4.69 5 6.18 4.26 8ZM13.46 8H15.74C14.99 6.18 13.73 4.69 12.07 3.86C12.74 5.1 13.23 6.5 13.46 8ZM4.26 12C5 13.82 6.27 15.31 7.93 16.14C7.26 14.9 6.77 13.5 6.54 12H4.26ZM13.46 12C13.23 13.5 12.74 14.9 12.07 16.14C13.73 15.31 14.99 13.82 15.74 12H13.46Z" fill="currentColor"/>
                    </svg>
                    <span class="current-locale-code">${currentLocale.toUpperCase()}</span>
                    <svg class="dropdown-arrow" width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path d="M2 4L6 8L10 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
                <div class="language-dropdown" id="language-dropdown">
                    <div class="language-dropdown-header">
                        <span data-i18n="language.change_language">Change Language</span>
                    </div>
                    <div class="language-list">
                        ${this.locales.map(locale => this.createLocaleItem(locale, currentLocale)).join('')}
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;

        // Add event listeners
        this.attachEventListeners();
    }

    /**
     * Create HTML for a locale item
     */
    createLocaleItem(locale, currentLocale) {
        const isActive = locale.code === currentLocale;
        const activeClass = isActive ? 'active' : '';

        return `
            <button class="language-item ${activeClass}"
                    data-locale="${locale.code}"
                    ${isActive ? 'aria-current="true"' : ''}>
                <span class="language-name">${locale.name}</span>
                <span class="language-code">${locale.code}</span>
                ${isActive ? '<span class="language-checkmark">✓</span>' : ''}
            </button>
        `;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const btn = document.getElementById('language-selector-btn');
        const dropdown = document.getElementById('language-dropdown');

        if (!btn || !dropdown) return;

        // Toggle dropdown
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.language-selector')) {
                dropdown.classList.remove('show');
            }
        });

        // Handle locale selection
        dropdown.querySelectorAll('.language-item').forEach(item => {
            item.addEventListener('click', () => {
                const locale = item.getAttribute('data-locale');
                this.selectLocale(locale);
                dropdown.classList.remove('show');
            });
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && dropdown.classList.contains('show')) {
                dropdown.classList.remove('show');
                btn.focus();
            }
        });
    }

    /**
     * Select a locale
     */
    async selectLocale(locale) {
        if (window.i18n) {
            await window.i18n.setLocale(locale);

            // Update the selector display
            this.updateSelected(locale);

            // Reload the page to apply translations to server-rendered content
            // This ensures all content is properly translated
            setTimeout(() => {
                window.location.reload();
            }, 100);
        }
    }

    /**
     * Update the selected locale in the UI
     */
    updateSelected(locale) {
        // Update button text
        const localeCode = document.querySelector('.current-locale-code');
        if (localeCode) {
            localeCode.textContent = locale.toUpperCase();
        }

        // Update active state in dropdown
        document.querySelectorAll('.language-item').forEach(item => {
            const itemLocale = item.getAttribute('data-locale');
            if (itemLocale === locale) {
                item.classList.add('active');
                item.setAttribute('aria-current', 'true');

                // Add checkmark if not present
                if (!item.querySelector('.language-checkmark')) {
                    const checkmark = document.createElement('span');
                    checkmark.className = 'language-checkmark';
                    checkmark.textContent = '✓';
                    item.appendChild(checkmark);
                }
            } else {
                item.classList.remove('active');
                item.removeAttribute('aria-current');

                // Remove checkmark
                const checkmark = item.querySelector('.language-checkmark');
                if (checkmark) {
                    checkmark.remove();
                }
            }
        });

        // Update RTL direction if needed
        const isRTL = this.locales.find(l => l.code === locale)?.rtl || false;
        document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
    }
}

// Initialize language selector when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new LanguageSelector();
    });
} else {
    new LanguageSelector();
}

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LanguageSelector;
}
