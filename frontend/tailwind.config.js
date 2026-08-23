/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Minimalist brand palette (monochrome with a single accent)
        brand: {
          50:  '#f8fafc',
          100: '#f1f5f9',
          500: '#000000', // Black accent for light mode, or white for dark
          600: '#333333',
          900: '#0f172a',
        },
        surface: {
          900: '#ffffff', // Background (white)
          800: '#f8fafc', // Cards (very light gray)
          700: '#f1f5f9', // Hover states
          600: '#e2e8f0', // Borders
          500: '#cbd5e1',
          400: '#94a3b8',
        },
        risk: {
          low:       '#059669', // Muted green
          medium:    '#d97706', // Muted orange
          high:      '#dc2626', // Muted red
          protected: '#2563eb', // Muted blue
        },
        text: {
          main: '#000000',
          muted: '#64748b'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
