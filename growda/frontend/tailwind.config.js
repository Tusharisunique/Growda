/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ["Delius", "Arial", "sans-serif"],
      },
      colors: {
        blue: {
          50: '#FFFDF8',   // soft card background
          100: '#F5F5DC',  // page background
          200: '#E8DCC8',  // subtle borders / accents
          300: '#D9C3A4',
          400: '#C29B6E',
          500: '#8B5A2B',  // primary accent (used by buttons, headings)
          600: '#704623',
          700: '#55341A',
          800: '#3E2C12',
          900: '#261708',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        }
      }
    },
  },
  plugins: [],
}

