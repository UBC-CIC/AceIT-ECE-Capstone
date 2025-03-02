require("dotenv").config();

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
      colors: {
        primary: process.env.VITE_REACT_APP_THEME_COLOUR_PRIMARY,
        secondary: process.env.VITE_REACT_APP_THEME_COLOUR_SECONDARY,
        tertiary: process.env.VITE_REACT_APP_THEME_COLOUR_TERTIARY,
        disabled: process.env.VITE_REACT_APP_THEME_COLOUR_DISABLED,
      },
    },
  },
  plugins: [],
};
