const { colors } = require("./theme.js");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  safelist: [
    "bg-primary",
    "bg-secondary",
    "bg-tertiary",
    "bg-disabled",
    "text-primary",
    "text-secondary",
    "text-tertiary",
    "text-disabled",
    "border-primary",
    "border-secondary",
    "border-tertiary",
    "border-disabled",
  ],
  theme: {
    extend: {
      colors,
    },
  },
  plugins: [],
};
