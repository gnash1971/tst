/*
 * Configuration Tailwind du Play CDN (mode développement).
 * FICHIER GÉNÉRÉ par scripts/build_index.py depuis data/brand-theme.json.
 * Ne pas éditer à la main : modifier data/brand-theme.json puis
 * régénérer (python scripts/build_index.py).
 * À charger après https://cdn.tailwindcss.com.
 */
tailwind.config = {
    "darkMode": "class",
    "theme": {
        "extend": {
            "colors": {
                "brand": {
                    "court": "#15803d",
                    "courtLight": "#22c55e",
                    "ball": "#f97316",
                    "navy": "#0f172a",
                    "admin": "#059669",
                    "adminLight": "#34d399",
                    "legal": "#ea580c",
                    "legalLight": "#fb923c",
                    "purple": "#8e44ad",
                    "blue": "#2980b9",
                    "green": "#16a34a",
                    "red": "#e74c3c"
                }
            },
            "fontFamily": {
                "sans": [
                    "Inter",
                    "Segoe UI",
                    "system-ui",
                    "sans-serif"
                ],
                "display": [
                    "Exo 2",
                    "Inter",
                    "system-ui",
                    "sans-serif"
                ]
            }
        }
    }
};
