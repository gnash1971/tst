/**
 * Repérage actif (scrollspy) : met en évidence le document en cours de lecture
 * dans les sommaires (vestiaire desktop et sommaire mobile) au fil du
 * défilement, sans jamais modifier l'URL (le hash reste géré par le
 * navigateur de documents).
 */
(function (global) {
    'use strict';

    var C = global.LTT.constants;

    function DocumentScrollSpy() {
        this.cards = document.querySelectorAll(C.SELECTORS.docCards);
        this.tocLinks = document.querySelectorAll(C.SELECTORS.tocLinks);
        this.mobileNav = document.querySelector(C.SELECTORS.docTocMobile);
        this.activeClass = C.TOC_ACTIVE_CLASS;
        this.activeId = null;
        this.visible = {};
        this.motionOk = !(
            global.matchMedia &&
            global.matchMedia('(prefers-reduced-motion: reduce)').matches
        );

        var supportsObserver = 'IntersectionObserver' in global;
        if (!supportsObserver || this.cards.length === 0 || this.tocLinks.length === 0) {
            return;
        }

        this.buildLinkMap();
        this.observe();
    }

    DocumentScrollSpy.prototype.buildLinkMap = function () {
        // Associe chaque identifiant de carte aux liens de sommaire pointant
        // vers elle (desktop et mobile peuvent coexister pour un même document).
        var map = {};
        this.tocLinks.forEach(function (link) {
            var href = link.getAttribute('href') || '';
            if (href.charAt(0) !== '#') {
                return;
            }
            var id = href.slice(1);
            if (!map[id]) {
                map[id] = [];
            }
            map[id].push(link);
        });
        this.linksById = map;
    };

    DocumentScrollSpy.prototype.observe = function () {
        var self = this;

        // Bande active resserrée en haut, sous les en-têtes collants.
        this.observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    self.visible[entry.target.id] = entry.isIntersecting;
                });
                self.updateActive();
            },
            { rootMargin: '-30% 0px -55% 0px', threshold: 0 }
        );

        this.cards.forEach(function (card) {
            if (card.id) {
                self.observer.observe(card);
            }
        });
    };

    DocumentScrollSpy.prototype.updateActive = function () {
        // Retient la première carte (ordre du DOM) présente dans la bande active.
        var nextId = null;
        for (var i = 0; i < this.cards.length; i += 1) {
            var id = this.cards[i].id;
            if (id && this.visible[id]) {
                nextId = id;
                break;
            }
        }

        if (nextId === this.activeId) {
            return;
        }
        this.setActive(nextId);
    };

    DocumentScrollSpy.prototype.setActive = function (id) {
        var self = this;

        this.tocLinks.forEach(function (link) {
            link.classList.remove(self.activeClass);
            link.removeAttribute('aria-current');
        });

        this.activeId = id;
        if (!id || !this.linksById[id]) {
            return;
        }

        var mobileLink = null;
        this.linksById[id].forEach(function (link) {
            link.classList.add(self.activeClass);
            link.setAttribute('aria-current', 'location');
            if (self.mobileNav && self.mobileNav.contains(link)) {
                mobileLink = link;
            }
        });

        if (mobileLink) {
            this.centerActiveLink(mobileLink);
        }
    };

    DocumentScrollSpy.prototype.centerActiveLink = function (link) {
        // Recentre la puce active dans la barre mobile sans faire défiler la page.
        var container = this.mobileNav;
        if (!container || container.scrollWidth <= container.clientWidth) {
            return;
        }

        var target =
            link.offsetLeft - (container.clientWidth - link.offsetWidth) / 2;
        container.scrollTo({
            left: Math.max(0, target),
            behavior: this.motionOk ? 'smooth' : 'auto',
        });
    };

    global.LTT = global.LTT || {};
    global.LTT.DocumentScrollSpy = DocumentScrollSpy;
})(window);
