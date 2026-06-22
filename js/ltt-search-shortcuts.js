/**
 * Raccourcis clavier de la recherche : « / » place le focus dans la barre,
 * « Échap » efface la requête. Gère aussi la visibilité de l'indice « / ».
 */
(function (global) {
    'use strict';

    var C = global.LTT.constants;

    function SearchShortcuts() {
        this.searchBar = document.querySelector(C.SELECTORS.searchBar);
        this.hint = document.querySelector(C.SELECTORS.searchKbdHint);

        if (this.searchBar) {
            this.bindEvents();
            this.updateHint();
        }
    }

    SearchShortcuts.prototype.isEditableTarget = function (element) {
        if (!element) {
            return false;
        }
        var tag = element.tagName;
        return (
            tag === 'INPUT' ||
            tag === 'TEXTAREA' ||
            tag === 'SELECT' ||
            element.isContentEditable === true
        );
    };

    SearchShortcuts.prototype.updateHint = function () {
        if (!this.hint) {
            return;
        }
        // L'indice s'efface dès que la recherche est active ou renseignée.
        var hide =
            document.activeElement === this.searchBar ||
            this.searchBar.value.length > 0;
        this.hint.classList.toggle('is-hidden', hide);
    };

    SearchShortcuts.prototype.clearSearch = function () {
        // Réutilise la logique existante du filtre via l'événement « input ».
        this.searchBar.value = '';
        this.searchBar.dispatchEvent(new Event('input', { bubbles: true }));
    };

    SearchShortcuts.prototype.handleKeydown = function (event) {
        // « / » : focus rapide, sauf si l'on saisit déjà du texte ailleurs.
        if (event.key === '/' && !this.isEditableTarget(event.target)) {
            event.preventDefault();
            this.searchBar.focus();
            return;
        }

        // « Échap » : efface la requête, sinon quitte le champ.
        if (event.key === 'Escape' && document.activeElement === this.searchBar) {
            if (this.searchBar.value.length > 0) {
                event.preventDefault();
                this.clearSearch();
            } else {
                this.searchBar.blur();
            }
        }
    };

    SearchShortcuts.prototype.bindEvents = function () {
        var self = this;

        document.addEventListener('keydown', function (event) {
            self.handleKeydown(event);
        });

        ['focus', 'blur', 'input'].forEach(function (eventName) {
            self.searchBar.addEventListener(eventName, function () {
                self.updateHint();
            });
        });
    };

    global.LTT = global.LTT || {};
    global.LTT.SearchShortcuts = SearchShortcuts;
})(window);
