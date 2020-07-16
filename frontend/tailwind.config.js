const defaultTheme = require("tailwindcss/defaultTheme");

module.exports = {
  purge: {
    enabled: process.env.NODE_ENV === "production",
    content: ["../awards/**/*.html"],
  },
  theme: {
    extend: {
      colors: {
        "blue-100": "#0d1530",
        "blue-200": "#1c2b5a",
        "blue-300": "#1f377a",
        "blue-400": "#1952b3",
        "blue-500": "#0d59f2",
        "blue-600": "#3b80f7",
        "blue-700": "#6ea5f7",
        "blue-800": "#a7c3fb",
        "blue-900": "#cfdefc",
      },
      fontFamily: {
        sans: ["Inter var", ...defaultTheme.fontFamily.sans],
      },
    },
    container: {
      center: true,
    },
  },
  variants: {},
  plugins: [require("@tailwindcss/ui"), require("@tailwindcss/custom-forms")],
};
