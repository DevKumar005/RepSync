const c = (n) => `rgb(var(--${n}) / <alpha-value>)`
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {
    colors: Object.fromEntries(['ink','ink-muted','paper','surface','line','brand','brandsoft','onbrand','neg','negsoft','pos','possoft','warn','warnsoft','fetchbg','fetchfg','glow'].map((n) => [n, c(n)])),
    fontFamily: { display:['"Inter"','sans-serif'], body:['"Inter"','sans-serif'], mono:['"IBM Plex Mono"','monospace'] },
    borderRadius: { '2xl': '16px', '3xl': '20px' },
  } }
}
