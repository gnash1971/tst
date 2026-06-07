/**
 * Application immédiate du thème (dans <head>, avant le rendu du body).
 */
(function () {
    'use strict';

    try {
        window.LTT.theme.apply(window.LTT.theme.resolveInitial());
    } catch (error) {
        document.documentElement.setAttribute('data-theme', 'light');
        document.documentElement.classList.remove('dark');
    }
})();
