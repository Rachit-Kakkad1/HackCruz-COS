/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cos: {
          bg: '#0f0f1a',
          surface: '#1a1a2e',
          accent1: '#6E7CFF',
          accent2: '#9A7BFF',
          text: '#E5E7EB',
          textMuted: '#9CA3AF'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
