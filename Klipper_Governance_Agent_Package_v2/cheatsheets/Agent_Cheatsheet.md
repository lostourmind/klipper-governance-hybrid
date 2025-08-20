## Klipper Macro Rules (Quick)
- Use `{var}` only inside strings/G-code. **Never** `{{ … }}`.
- Do math/round/casts in `{% set … %}`; inject the result as `{var}`.
- No inline `{% if %}{% set %}{% endif %}` on one line.
- RESPOND-only; no `;` or `[]` in messages; ASCII-only.
- Use `SAVE_VARIABLE`/`SET_GCODE_VARIABLE` for state.
