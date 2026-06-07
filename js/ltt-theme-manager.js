/**
 * Gestionnaire du bouton de bascule de thème.
 */
(function (global) {
    'use strict';

    var SELECTOR = global.LTT.constants.SELECTORS.themeToggle;

    function ThemeManager() {
        this.toggleButton = document.querySelector(SELECTOR);
        if (this.toggleButton) {
            this.bindEvents();
        }
    }

    ThemeManager.prototype.bindEvents = function () {
        var self = this;
        this.toggleButton.addEventListener('click', function () {
            global.LTT.theme.toggle();
        });
    };

    global.LTT = global.LTT || {};
    global.LTT.ThemeManager = ThemeManager;
})(window);
