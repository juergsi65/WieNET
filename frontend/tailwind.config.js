/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        display: ["'Space Grotesk'", "system-ui", "sans-serif"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      colors: {
        ink: {
          DEFAULT: "#14171A",
          50: "#f4f5f6",
          100: "#e4e6e8",
          400: "#6b7580",
          600: "#3a4750",
          800: "#20262b",
          900: "#14171A",
        },
        paper: {
          DEFAULT: "#F7F6F3",
          dim: "#EFEDE8",
        },
        blueprint: {
          DEFAULT: "#1B2A3A",
          800: "#152230",
          900: "#0F1922",
        },
        // Conduit: Baustellen-/Signalorange, zugleich Glasfaser-Industriefarbe für Rohr 1
        conduit: {
          50: "#fff3ec",
          100: "#ffe1cf",
          300: "#ff9d5c",
          500: "#E8590C",
          600: "#c94a08",
          700: "#a53c07",
        },
        // Signal: sekundäres Teal, Lichtwellenleiter-Anmutung
        signal: {
          50: "#e9f7f6",
          100: "#c9ebe9",
          300: "#5bb8b5",
          500: "#0E7C7B",
          600: "#0b6362",
          700: "#094f4e",
        },
        // "brand" bleibt als Alias bestehen, damit ältere Komponenten weiterfunktionieren,
        // zeigt jetzt aber auf die neue Signalfarbe statt generischem Blau.
        brand: {
          50: "#e9f7f6",
          100: "#c9ebe9",
          300: "#5bb8b5",
          500: "#0E7C7B",
          600: "#0b6362",
          700: "#094f4e",
          900: "#0F1922",
        },
      },
      boxShadow: {
        panel: "0 1px 2px rgba(20,23,26,0.06), 0 4px 16px rgba(20,23,26,0.06)",
      },
    },
  },
  plugins: [],
};
