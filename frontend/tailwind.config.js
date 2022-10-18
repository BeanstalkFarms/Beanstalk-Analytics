const colors = require('tailwindcss/colors')

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      red: colors.red, 
      yellow: colors.yellow, 
      green: colors.green, 
      emerald: colors.emerald, 
      slate: colors.slate,
      blue: colors.blue, 
      gray: colors.gray, 
      orange: colors.orange, 
      white: colors.white, 
    },
  },
  plugins: [
    // Or with a custom prefix:
    require('@headlessui/tailwindcss')({ prefix: 'ui' })
  ],
}
