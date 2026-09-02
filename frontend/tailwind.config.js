/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Odoo's own palette. Business software has a visual grammar its users
        // already read fluently, and borrowing it is cheaper for them than
        // teaching a new one.
        primary: "#714B67",
        "primary-dark": "#5C3D54",
        "primary-tint": "#F3EEF2",
        accent: "#017E84",
        "accent-dark": "#016268",
        canvas: "#F9F9F9",
        sheet: "#FFFFFF",
        "sheet-border": "#DFDFDF",
        muted: "#6B7280",
        ink: "#374151",
        "status-created": "#5A6B7C",
        "status-created-tint": "#EDF1F5",
        "status-validated": "#1F7A3D",
        "status-validated-tint": "#E8F5EC",
        "status-refused": "#B3261E",
        "status-refused-tint": "#FBEAE8",
        "status-processed": "#714B67",
        "status-processed-tint": "#F3EEF2",
      },
      fontFamily: {
        // No webfont is fetched, so the application renders identically on a
        // machine with no network access.
        sans: ["Roboto", "Segoe UI", "system-ui", "-apple-system", "sans-serif"],
      },
      boxShadow: {
        sheet: "0 1px 3px rgba(0, 0, 0, 0.08)",
        dialog: "0 10px 40px rgba(0, 0, 0, 0.20)",
      },
    },
  },
  plugins: [],
};
