/**
 * @file app.js
 * @description Point d'entrée : icônes Lucide et initialisation des modules LTT.
 */
(function (global) {
    'use strict';

    function initLucideIcons() {
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }
    }

    function bootstrap() {
        initLucideIcons();

        new global.LTT.ThemeManager();
        var documentFilter = new global.LTT.DocumentFilter();
        new global.LTT.DocumentNavigator(documentFilter);

        if (global.LTT.DocumentScrollSpy) {
            new global.LTT.DocumentScrollSpy();
        }
        if (global.LTT.BackToTop) {
            new global.LTT.BackToTop();
        }
        if (global.LTT.SearchShortcuts) {
            new global.LTT.SearchShortcuts();
        }
    }

    document.addEventListener('DOMContentLoaded', bootstrap);
})(window);
