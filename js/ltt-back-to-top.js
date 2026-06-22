/**
 * Bouton flottant « retour en haut » : apparaît au-delà d'un seuil de
 * défilement et ramène la page en tête (défilement doux respectant la
 * préférence de mouvement réduit).
 */
(function (global) {
    'use strict';

    var C = global.LTT.constants;

    function BackToTop() {
        this.button = document.querySelector(C.SELECTORS.backToTop);
        this.offset = C.BACK_TO_TOP_OFFSET_PX || 600;
        this.ticking = false;
        this.motionOk = !(
            global.matchMedia &&
            global.matchMedia('(prefers-reduced-motion: reduce)').matches
        );

        if (this.button) {
            this.bindEvents();
            this.update();
        }
    }

    BackToTop.prototype.getScrollTop = function () {
        return global.pageYOffset || document.documentElement.scrollTop || 0;
    };

    BackToTop.prototype.update = function () {
        var visible = this.getScrollTop() > this.offset;
        this.button.classList.toggle('is-visible', visible);
        this.ticking = false;
    };

    BackToTop.prototype.onScroll = function () {
        // Limite les recalculs à une frame d'affichage.
        var self = this;
        if (this.ticking) {
            return;
        }
        this.ticking = true;
        global.requestAnimationFrame(function () {
            self.update();
        });
    };

    BackToTop.prototype.scrollToTop = function () {
        global.scrollTo({
            top: 0,
            behavior: this.motionOk ? 'smooth' : 'auto',
        });

        // Replace le focus en tête pour les utilisateurs clavier / lecteur d'écran.
        var home = document.querySelector('.site-header a[href]');
        if (home && typeof home.focus === 'function') {
            home.focus({ preventScroll: true });
        }
    };

    BackToTop.prototype.bindEvents = function () {
        var self = this;
        global.addEventListener(
            'scroll',
            function () {
                self.onScroll();
            },
            { passive: true }
        );
        this.button.addEventListener('click', function () {
            self.scrollToTop();
        });
    };

    global.LTT = global.LTT || {};
    global.LTT.BackToTop = BackToTop;
})(window);
