/**
 * @file ltt-document-theme.js
 * @description Gère l'initialisation et la bascule de thème clair/sombre pour les pages de documents officiels (fic/).
 * Élimine le besoin de scripts inline pour une sécurité CSP optimale.
 *
 * @author Lentilly Tennis de Table
 * @copyright 2026
 */
(function (global) {
    'use strict';

    /**
     * Gère la bascule entre le mode clair et le mode sombre pour une page de document.
     * Persiste la préférence utilisateur dans le stockage local et
     * synchronise l'état accessible (aria-pressed) du bouton.
     * @constructor
     */
    function ThemeToggle() {
        this.button = document.getElementById('theme-toggle');
        if (!this.button) {
            return;
        }
        this.storageKey = 'theme-preference';
        this.init();
    }

    /**
     * Lit le thème courant à partir de l'attribut `data-theme`.
     * @returns {'light'|'dark'} Le thème actif.
     */
    ThemeToggle.prototype.getCurrentTheme = function () {
        return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    };

    /**
     * Applique le thème souhaité au document et synchronise l'état accessible du bouton.
     * @param {'light'|'dark'} theme - Le thème à appliquer.
     */
    ThemeToggle.prototype.applyTheme = function (theme) {
        var safeTheme = theme === 'dark' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', safeTheme);
        
        if (this.button) {
            this.button.setAttribute('aria-pressed', safeTheme === 'dark' ? 'true' : 'false');
            this.button.setAttribute(
                'title',
                safeTheme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'
            );
        }
    };

    /**
     * Persiste la préférence utilisateur dans le localStorage.
     * @param {'light'|'dark'} theme - Le thème à sauvegarder.
     */
    ThemeToggle.prototype.persistTheme = function (theme) {
        try {
            global.localStorage.setItem(this.storageKey, theme);
        } catch (e) {
            /* Stockage indisponible (ex: navigation privée stricte) : on ignore silencieusement. */
        }
    };

    /**
     * Initialise l'état et attache l'écouteur de clic.
     */
    ThemeToggle.prototype.init = function () {
        var self = this;
        this.applyTheme(this.getCurrentTheme());
        this.button.addEventListener('click', function () {
            var next = self.getCurrentTheme() === 'dark' ? 'light' : 'dark';
            self.applyTheme(next);
            self.persistTheme(next);
        });
    };

    // Initialisation globale au chargement du DOM
    document.addEventListener('DOMContentLoaded', function () {
        new ThemeToggle();
    });

})(window);
