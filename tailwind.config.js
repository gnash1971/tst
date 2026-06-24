/** @type {import('tailwindcss').Config} */

// Source unique du thème (couleurs de marque + polices), partagée avec la
// configuration du Play CDN (js/tailwind.config.js, générée au build).
// Regroupements des couleurs brand : court/courtLight/ball/navy (identité),
// admin/adminLight/legal/legalLight (accents par catégorie de documents),
// purple/blue/green/red (rappels d'identité des documents fic/*.html).
const brandTheme = require("./data/brand-theme.json");

module.exports = {
  content: [
    "./index.html",
    "./index.template.html",
    "./partials/**/*.html",
    "./fic/**/*.html",
    "./js/**/*.js"
  ],
  darkMode: 'class',
  theme: {
    extend: brandTheme,
  },
  plugins: [],
}
