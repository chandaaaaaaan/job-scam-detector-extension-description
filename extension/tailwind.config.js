module.exports = {
  darkMode: "class",
  content: ["./*.html", "./*.js"],
  theme: {
      extend: {
          colors: {
              "surface-container-high": "#262a2f",
              "surface-container-low": "#181c20",
              "outline": "#849495",
              "on-surface-variant": "#b9cacb",
              "on-surface": "#e0e3e8",
              "background": "#101418",
              "outline-variant": "#3a494b",
              "surface-container-lowest": "#0a0f13",
              "surface-container": "#1c2024",
              "surface-container-highest": "#31353a",
              "primary": "#00f2ff",
              "ignition-theme": "rgba(var(--theme-color-rgb), <alpha-value>)"
          },
          fontFamily: {
              "headline": ["Space Grotesk", "sans-serif"],
              "body": ["Inter", "sans-serif"],
              "label": ["Inter", "sans-serif"]
          }
      }
  }
}
