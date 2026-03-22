import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#E8593F",
          dark: "#C74532",
          light: "#FDEAE6",
        },
        secondary: {
          DEFAULT: "#2D3142",
          light: "#4F5565",
        },
        accent: {
          DEFAULT: "#F4A236",
          light: "#FFF3E0",
        },
        background: "var(--background)",
        foreground: "var(--foreground)",
      },
    },
  },
  plugins: [],
};
export default config;
