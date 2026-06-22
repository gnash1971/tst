/**
 * Recherche textuelle et filtrage par catégorie des cartes documentaires.
 */
(function (global) {
    'use strict';

    var C = global.LTT.constants;

    function DocumentFilter() {
        this.searchBar = document.querySelector(C.SELECTORS.searchBar);
        this.clearSearchBtn = document.querySelector(C.SELECTORS.clearSearch);
        this.docCards = document.querySelectorAll(C.SELECTORS.docCards);
        this.filterButtons = document.querySelectorAll(C.SELECTORS.filterButtons);
        this.noResults = document.querySelector(C.SELECTORS.noResults);
        this.resetSearchBtn = document.querySelector(C.SELECTORS.resetSearch);
        this.docCount = document.querySelector(C.SELECTORS.docCount);

        this.currentCategory = C.CATEGORY_ALL;
        this.searchQuery = '';

        if (this.searchBar && this.docCards.length > 0) {
            this.bindEvents();
            this.renderCategoryCounts();
        }
    }

    DocumentFilter.prototype.getQueryWords = function () {
        return this.searchQuery
            .toLowerCase()
            .split(/\s+/)
            .filter(function (word) {
                return word.length > 0;
            });
    };

    DocumentFilter.prototype.cardMatchesSearch = function (card, queryWords) {
        if (queryWords.length === 0) {
            return true;
        }

        var cardSearchText = (card.getAttribute('data-search') || '').toLowerCase();
        var titleElement = card.querySelector('h3');
        var descElement = card.querySelector('p');
        var titleText = titleElement ? titleElement.textContent.toLowerCase() : '';
        var descText = descElement ? descElement.textContent.toLowerCase() : '';

        return queryWords.every(function (word) {
            return (
                cardSearchText.includes(word) ||
                titleText.includes(word) ||
                descText.includes(word)
            );
        });
    };

    DocumentFilter.prototype.cardMatchesCategory = function (card) {
        return (
            this.currentCategory === C.CATEGORY_ALL ||
            card.getAttribute('data-category') === this.currentCategory
        );
    };

    DocumentFilter.prototype.updateDocCount = function (matchCount) {
        if (!this.docCount) {
            return;
        }

        var label =
            matchCount > 1 ? 'documents disponibles' : 'document disponible';
        this.docCount.textContent = matchCount + ' ' + label;
    };

    DocumentFilter.prototype.updateNoResults = function (matchCount) {
        if (!this.noResults) {
            return;
        }

        this.noResults.classList.toggle('hidden', matchCount > 0);
    };

    DocumentFilter.prototype.setFilterButtonState = function (button, isActive) {
        if (isActive) {
            button.classList.add.apply(button.classList, C.FILTER_BTN_ACTIVE);
            button.classList.remove.apply(
                button.classList,
                C.FILTER_BTN_INACTIVE
            );
            return;
        }

        button.classList.remove.apply(button.classList, C.FILTER_BTN_ACTIVE);
        button.classList.add.apply(button.classList, C.FILTER_BTN_INACTIVE);
    };

    DocumentFilter.prototype.activateCategory = function (category) {
        var self = this;
        this.currentCategory = category;

        this.filterButtons.forEach(function (button) {
            var buttonCategory = button.getAttribute('data-category');
            self.setFilterButtonState(button, buttonCategory === category);
        });
    };

    DocumentFilter.prototype.clearSearchInput = function () {
        if (this.searchBar) {
            this.searchBar.value = '';
        }
        this.searchQuery = '';

        if (this.clearSearchBtn) {
            this.clearSearchBtn.classList.add('hidden');
        }
    };

    DocumentFilter.prototype.updateClearButtonVisibility = function () {
        if (!this.clearSearchBtn) {
            return;
        }

        var hasQuery = this.searchQuery.trim().length > 0;
        this.clearSearchBtn.classList.toggle('hidden', !hasQuery);
    };

    DocumentFilter.prototype.filterDocuments = function (animate) {
        var self = this;
        var matchCount = 0;
        var queryWords = this.getQueryWords();
        var motionOk = !(
            window.matchMedia &&
            window.matchMedia('(prefers-reduced-motion: reduce)').matches
        );

        this.docCards.forEach(function (card) {
            var isVisible =
                self.cardMatchesCategory(card) &&
                self.cardMatchesSearch(card, queryWords);

            card.style.display = isVisible ? 'flex' : 'none';
            if (isVisible) {
                matchCount += 1;
                if (animate && motionOk) {
                    self.replayEnterAnimation(card);
                }
            }
        });

        this.updateNoResults(matchCount);
        this.updateDocCount(matchCount);
    };

    DocumentFilter.prototype.replayEnterAnimation = function (card) {
        // Relance l'animation d'apparition : on retire la classe, on force un
        // reflow, puis on la réapplique (même technique que le navigateur de
        // cartes pour redémarrer une animation CSS déjà jouée).
        card.classList.remove(C.CARD_ENTER_CLASS);
        void card.offsetWidth;
        card.classList.add(C.CARD_ENTER_CLASS);
    };

    DocumentFilter.prototype.renderCategoryCounts = function () {
        var self = this;
        if (!this.filterButtons || this.filterButtons.length === 0) {
            return;
        }

        this.filterButtons.forEach(function (button) {
            var category = button.getAttribute('data-category');
            var count = 0;

            if (!category || category === C.CATEGORY_ALL) {
                count = self.docCards.length;
            } else {
                self.docCards.forEach(function (card) {
                    if (card.getAttribute('data-category') === category) {
                        count += 1;
                    }
                });
            }

            // Pastille décorative (masquée aux technologies d'assistance pour
            // conserver un nom accessible stable sur le bouton de filtre).
            var badge = button.querySelector('.' + C.FILTER_COUNT_CLASS);
            if (!badge) {
                badge = document.createElement('span');
                badge.className = C.FILTER_COUNT_CLASS;
                badge.setAttribute('aria-hidden', 'true');
                button.appendChild(badge);
            }
            badge.textContent = String(count);
        });
    };

    DocumentFilter.prototype.resetFilters = function () {
        this.clearSearchInput();
        this.activateCategory(C.CATEGORY_ALL);
        this.filterDocuments(true);
    };

    DocumentFilter.prototype.revealDocumentCard = function (cardId) {
        var card = document.getElementById(cardId);
        if (!card) {
            return null;
        }

        if (card.style.display === 'none') {
            this.resetFilters();
        }

        return card;
    };

    DocumentFilter.prototype.bindEvents = function () {
        var self = this;

        this.searchBar.addEventListener('input', function (event) {
            self.searchQuery = event.target.value;
            self.updateClearButtonVisibility();
            self.filterDocuments();
        });

        if (this.clearSearchBtn) {
            this.clearSearchBtn.addEventListener('click', function () {
                self.clearSearchInput();
                self.searchBar.focus();
                self.filterDocuments();
            });
        }

        this.filterButtons.forEach(function (button) {
            button.addEventListener('click', function () {
                var targetCategory = button.getAttribute('data-category');
                if (!targetCategory) {
                    return;
                }

                self.activateCategory(targetCategory);
                self.filterDocuments(true);
            });
        });

        if (this.resetSearchBtn) {
            this.resetSearchBtn.addEventListener('click', function () {
                self.resetFilters();
            });
        }
    };

    global.LTT = global.LTT || {};
    global.LTT.DocumentFilter = DocumentFilter;
})(window);
