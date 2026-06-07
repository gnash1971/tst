/**
 * Navigation du sommaire (vestiaire numérique) vers les cartes documentaires.
 */
(function (global) {
    'use strict';

    var C = global.LTT.constants;

    /** @param {object} documentFilter Filtre partagé des cartes documentaires. */
    function DocumentNavigator(documentFilter) {
        this.documentFilter = documentFilter;
        this.tocLinks = document.querySelectorAll(C.SELECTORS.tocLinks);
        this.highlightClass = C.HIGHLIGHT_CLASS;
        this.highlightDurationMs = C.HIGHLIGHT_DURATION_MS;

        if (this.tocLinks.length > 0) {
            this.bindEvents();
            this.handleInitialHash();
        }
    }

    DocumentNavigator.prototype.highlightCard = function (card) {
        card.classList.remove(this.highlightClass);
        void card.offsetWidth;
        card.classList.add(this.highlightClass);

        var self = this;
        window.setTimeout(function () {
            card.classList.remove(self.highlightClass);
        }, this.highlightDurationMs);
    };

    DocumentNavigator.prototype.isValidCardId = function (cardId) {
        return /^[a-z][a-z0-9-]*$/.test(cardId);
    };

    DocumentNavigator.prototype.navigateToCard = function (cardId) {
        if (!this.isValidCardId(cardId)) {
            return;
        }

        var card = this.documentFilter.revealDocumentCard(cardId);
        if (!card) {
            return;
        }

        card.scrollIntoView({ behavior: 'smooth', block: 'start' });
        this.highlightCard(card);

        if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', '#' + cardId);
        }
    };

    DocumentNavigator.prototype.bindEvents = function () {
        var self = this;

        this.tocLinks.forEach(function (link) {
            link.addEventListener('click', function (event) {
                var href = link.getAttribute('href');
                if (!href || href.charAt(0) !== '#') {
                    return;
                }

                event.preventDefault();
                self.navigateToCard(href.slice(1));
            });
        });
    };

    DocumentNavigator.prototype.handleInitialHash = function () {
        var cardId = window.location.hash.replace('#', '');
        if (!cardId || !this.isValidCardId(cardId) || !document.getElementById(cardId)) {
            return;
        }

        var self = this;
        window.requestAnimationFrame(function () {
            self.navigateToCard(cardId);
        });
    };

    global.LTT = global.LTT || {};
    global.LTT.DocumentNavigator = DocumentNavigator;
})(window);
