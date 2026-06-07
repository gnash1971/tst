/**
 * Constantes partagées de l'interface documentaire.
 */
(function (global) {
    'use strict';

    global.LTT = global.LTT || {};
    global.LTT.constants = {
        CATEGORY_ALL: 'all',
        FILTER_BTN_ACTIVE: [
            'active',
            'bg-emerald-600',
            'text-white',
            'shadow-md',
            'shadow-emerald-500/20',
            'border-emerald-600',
        ],
        FILTER_BTN_INACTIVE: [
            'bg-white',
            'dark:bg-slate-800',
            'border-slate-200',
            'dark:border-slate-600',
            'text-slate-700',
            'dark:text-slate-200',
            'hover:bg-slate-50',
            'dark:hover:bg-slate-700',
        ],
        HIGHLIGHT_CLASS: 'doc-card--highlight',
        HIGHLIGHT_DURATION_MS: 2200,
        SELECTORS: {
            themeToggle: '#theme-toggle',
            searchBar: '#search-bar',
            clearSearch: '#clear-search',
            resetSearch: '#reset-search',
            docCards: '.doc-card',
            filterButtons: '.filter-btn',
            noResults: '#no-results',
            docCount: '#doc-count',
            tocLinks: '.doc-toc-link',
        },
    };
})(window);
