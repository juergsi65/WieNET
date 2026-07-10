/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff9ff", 100: "#def2ff", 300: "#7cd2ff", 500: "#1aa0e8",
          600: "#0d80c2", 700: "#0c649a", 900: "#0d2d47",
        },
      },
    },
  },
  plugins: [],
};
