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
    }

    document.addEventListener('DOMContentLoaded', bootstrap);
})(window);
