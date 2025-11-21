/**
 * Internationalization (i18n) System
 *
 * Provides translation support for the Product Knowledge Graph Manager.
 * Loads translation files from /static/i18n/ and provides functions to
 * translate UI strings based on the selected locale.
 */

class I18n {
    constructor() {
        this.translations = {};
        this.currentLocale = 'en';
        this.fallbackLocale = 'en';
        this.loadedLocales = new Set();
    }

    /**
     * Initialize the i18n system
     * Loads the locale from localStorage or uses default
     */
    async init() {
        // Get saved locale from localStorage or use default
        const savedLocale = localStorage.getItem('locale') || this.fallbackLocale;
        await this.setLocale(savedLocale);

        // Add event listener for locale changes
        window.addEventListener('localechange', (e) => {
            this.setLocale(e.detail.locale);
        });
    }

    /**
     * Load translation file for a locale
     * @param {string} locale - Locale code (e.g., 'en', 'es-ES')
     * @returns {Promise<Object>} Translation data
     */
    async loadTranslations(locale) {
        if (this.loadedLocales.has(locale)) {
            return this.translations[locale];
        }

        try {
            const response = await fetch(`/static/i18n/${locale}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load translations for ${locale}`);
            }

            const data = await response.json();
            this.translations[locale] = data;
            this.loadedLocales.add(locale);

            console.log(`Loaded translations for ${locale}`);
            return data;
        } catch (error) {
            console.error(`Error loading translations for ${locale}:`, error);

            // Fallback to English if not already loaded
            if (locale !== this.fallbackLocale && !this.loadedLocales.has(this.fallbackLocale)) {
                return this.loadTranslations(this.fallbackLocale);
            }

            return {};
        }
    }

    /**
     * Set the current locale
     * @param {string} locale - Locale code
     */
    async setLocale(locale) {
        await this.loadTranslations(locale);

        // Ensure fallback locale is also loaded
        if (locale !== this.fallbackLocale) {
            await this.loadTranslations(this.fallbackLocale);
        }

        this.currentLocale = locale;
        localStorage.setItem('locale', locale);

        // Update HTML lang attribute
        document.documentElement.lang = locale;

        // Trigger translation update
        this.translatePage();

        // Dispatch event for other components
        window.dispatchEvent(new CustomEvent('localechanged', { detail: { locale } }));

        console.log(`Locale set to: ${locale}`);
    }

    /**
     * Get current locale
     * @returns {string} Current locale code
     */
    getLocale() {
        return this.currentLocale;
    }

    /**
     * Translate a key
     * @param {string} key - Translation key (e.g., 'nav.home', 'dashboard.title')
     * @param {Object} vars - Variables for substitution (e.g., {page: 1, total: 10})
     * @returns {string} Translated string
     */
    t(key, vars = {}) {
        // Split key into parts (e.g., 'nav.home' -> ['nav', 'home'])
        const keys = key.split('.');

        // Try to get translation from current locale
        let translation = this.getTranslation(keys, this.currentLocale);

        // Fallback to English if not found
        if (translation === undefined && this.currentLocale !== this.fallbackLocale) {
            translation = this.getTranslation(keys, this.fallbackLocale);
        }

        // Fallback to key if still not found
        if (translation === undefined) {
            console.warn(`Translation not found for key: ${key}`);
            return key;
        }

        // Substitute variables
        return this.substitute(translation, vars);
    }

    /**
     * Get translation from translations object
     * @param {Array} keys - Array of key parts
     * @param {string} locale - Locale code
     * @returns {string|undefined} Translation or undefined if not found
     */
    getTranslation(keys, locale) {
        const localeData = this.translations[locale];
        if (!localeData) return undefined;

        let current = localeData;
        for (const key of keys) {
            if (current[key] === undefined) {
                return undefined;
            }
            current = current[key];
        }

        return current;
    }

    /**
     * Substitute variables in translation string
     * @param {string} str - String with placeholders (e.g., "Page {page} of {total}")
     * @param {Object} vars - Variables to substitute
     * @returns {string} String with substituted values
     */
    substitute(str, vars) {
        return str.replace(/\{(\w+)\}/g, (match, key) => {
            return vars[key] !== undefined ? vars[key] : match;
        });
    }

    /**
     * Translate all elements with data-i18n attribute
     */
    translatePage() {
        // Translate text content
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const vars = this.parseDataVars(element);
            element.textContent = this.t(key, vars);
        });

        // Translate placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });

        // Translate titles
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });

        // Translate aria-label
        document.querySelectorAll('[data-i18n-aria]').forEach(element => {
            const key = element.getAttribute('data-i18n-aria');
            element.setAttribute('aria-label', this.t(key));
        });
    }

    /**
     * Parse data-i18n-vars attribute
     * @param {Element} element - DOM element
     * @returns {Object} Variables object
     */
    parseDataVars(element) {
        const varsAttr = element.getAttribute('data-i18n-vars');
        if (!varsAttr) return {};

        try {
            return JSON.parse(varsAttr);
        } catch (error) {
            console.error('Error parsing data-i18n-vars:', error);
            return {};
        }
    }

    /**
     * Get list of available locales
     * @returns {Array} Array of locale codes
     */
    getAvailableLocales() {
        return ['en', 'ar', 'de', 'es-ES', 'fr', 'pt-BR', 'zh-CN'];
    }

    /**
     * Get locale display name
     * @param {string} locale - Locale code
     * @returns {string} Display name
     */
    getLocaleDisplayName(locale) {
        const names = {
            'en': 'English',
            'ar': 'العربية',
            'de': 'Deutsch',
            'es-ES': 'Español',
            'fr': 'Français',
            'pt-BR': 'Português (Brasil)',
            'zh-CN': '中文 (简体)'
        };
        return names[locale] || locale;
    }

    /**
     * Check if locale is RTL (right-to-left)
     * @param {string} locale - Locale code
     * @returns {boolean} True if RTL
     */
    isRTL(locale) {
        return locale === 'ar';
    }
}

// Create global i18n instance
window.i18n = new I18n();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.i18n.init());
} else {
    window.i18n.init();
}

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = I18n;
}
