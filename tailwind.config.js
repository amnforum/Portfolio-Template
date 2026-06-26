/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./core/templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'portfolio-orange': '#ea580c',
        'portfolio-dark':   '#0a0a0a',
        'portfolio-darker': '#060606',
        'portfolio-charcoal': '#111111',
        'portfolio-gold':   '#f59e0b',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
    },
  },
  plugins: [],
}
