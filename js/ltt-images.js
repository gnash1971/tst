/**
 * Gestion des repli logo sans gestionnaires inline (compatibilité CSP stricte).
 */
(function () {
    'use strict';

    var FALLBACK_SVG =
        'data:image/svg+xml;charset=utf-8,' +
        '%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20' +
        'viewBox%3D%220%200%20100%20100%22%3E%3Ccircle%20cx%3D%2250%22%20' +
        'cy%3D%2250%22%20r%3D%2240%22%20fill%3D%22%232c3e50%22%2F%3E%3Ctext%20' +
        'x%3D%2250%25%22%20y%3D%2255%25%22%20dominant-baseline%3D%22middle%22%20' +
        'text-anchor%3D%22middle%22%20fill%3D%22white%22%20font-size%3D%2232%22%20' +
        'font-weight%3D%22bold%22%3ELTT%3C%2Ftext%3E%3C%2Fsvg%3E';

    function bindFallback(img, mode) {
        img.addEventListener(
            'error',
            function handleError() {
                img.removeEventListener('error', handleError);
                if (mode === 'svg') {
                    img.src = FALLBACK_SVG;
                    return;
                }
                img.style.display = 'none';
            }
        );
    }

    function initLogoImages() {
        document
            .querySelectorAll('img[data-logo-fallback="svg"]')
            .forEach(function (img) {
                bindFallback(img, 'svg');
            });

        document
            .querySelectorAll('img[data-logo-fallback="hide"]')
            .forEach(function (img) {
                bindFallback(img, 'hide');
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLogoImages);
    } else {
        initLogoImages();
    }
})();
