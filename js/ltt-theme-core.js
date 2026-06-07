/**
 * Utilitaires partagés de thème clair/sombre (namespace global LTT).
 */
(function (global) {
    'use strict';

    var STORAGE_KEY = 'theme-preference';
    var root = document.documentElement;

    /**
     * Applique le thème sur la racine HTML (attribut + classe Tailwind).
     * @param {'light'|'dark'} theme
     */
    function applyTheme(theme) {
        root.setAttribute('data-theme', theme);
        root.classList.toggle('dark', theme === 'dark');
    }

    /**
     * Détermine le thème initial (stockage local ou préférence système).
     * @returns {'light'|'dark'}
     */
    function resolveInitialTheme() {
        try {
            var stored = global.localStorage.getItem(STORAGE_KEY);
            if (stored === 'light' || stored === 'dark') {
                return stored;
            }
        } catch (error) {
            /* localStorage indisponible */
        }

        var prefersDark =
            global.matchMedia &&
            global.matchMedia('(prefers-color-scheme: dark)').matches;

        return prefersDark ? 'dark' : 'light';
    }

    /**
     * Persiste le choix utilisateur.
     * @param {'light'|'dark'} theme
     */
    function persistTheme(theme) {
        try {
            global.localStorage.setItem(STORAGE_KEY, theme);
        } catch (error) {
            /* Ignore si le stockage est bloqué */
        }
    }

    /**
     * Bascule entre clair et sombre.
     * @returns {'light'|'dark'} Nouveau thème actif.
     */
    function toggleTheme() {
        var current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        var next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        persistTheme(next);
        return next;
    }

    global.LTT = global.LTT || {};
    global.LTT.theme = {
        apply: applyTheme,
        resolveInitial: resolveInitialTheme,
        persist: persistTheme,
        toggle: toggleTheme,
    };
})(window);
