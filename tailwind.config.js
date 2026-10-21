const c = (n) => `rgb(var(--${n}) / <alpha-value>)`
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {
    colors: Object.fromEntries(['ink','paper','surface','line','brand','brandsoft','onbrand','neg','negsoft','pos','warn','warnsoft','fetchbg','fetchfg'].map((n) => [n, c(n)])),
    fontFamily: { display:['"Inter"','sans-serif'], body:['"Inter"','sans-serif'], mono:['"IBM Plex Mono"','monospace'] }
  } }
}
