/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./core/templates/**/*.html",
    "./ecozyhome/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        eco: {
          50:  '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          950: '#052e16',
        },
        sand: {
          50:  '#fefcf3',
          100: '#fdf6e3',
          200: '#faecc7',
          300: '#f5dda0',
          400: '#edc56e',
          500: '#e5ad45',
          600: '#d49530',
          700: '#b07727',
          800: '#8e5e26',
          900: '#754d22',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
