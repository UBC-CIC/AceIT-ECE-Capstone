import dotenv from "dotenv";
dotenv.config();

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
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
