# Klipper Governance Tooling v2
Priority-layered linter + hooks to *prevent* Klipper-incompatible macros from reaching your repo or printer.

## Layers (in this exact order)
- **P0 – Syntax Guards (hard fail)**
  - Ban `{{ ... }}` (double mustache) anywhere.
  - Ban pipes `|` inside single-brace injections `{ ... }` (e.g., `{x|round(2)}`).
  - Forbid inline control blocks on one line (`{% if %}{% set %}{% endif %}`).
  - Forbid `break`, `continue`, `{% return %}` in Jinja tags.
- **P1 – Klipper-Compat Rules (hard fail)**
  - Require precomputation with `{% set ... %}` for math/filters (no filters in `{ ... }`).
  - ASCII-only (optional strict).
  - No `M118` unless allowed.
- **P2 – Governance Hygiene (hard fail)**
  - No content below SAVE_CONFIG marker.
  - RESPOND-only: messages must not contain `;` or `[]` and must be under `gcode:` blocks.
- **P3 – Style & Nits (warn by default)**
  - Filter spacing suggestions, redundant casts, unicode quotes, etc.

## Files
- `tools/klipper_macro_lint.py`   – layered linter with severities & conflict hints
- `tools/klipper_macro_fix.py`    – safe auto-fixer for common cases (see below)
- `hooks/pre-commit`              – runs linter on `printer.cfg` and `macros/`
- `.klipperlint.toml`             – config (tune severities, allow M118, strict ASCII)

## Install
```bash
unzip Klipper_Governance_Tooling_v2.zip
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
# optional: run manually
python3 tools/klipper_macro_lint.py --paths printer.cfg macros/
```

## Auto-fix (safe subset)
Run:
```bash
python3 tools/klipper_macro_fix.py --paths printer.cfg macros/
```
What it does (only when unambiguous):
- Convert **`{{ var }}`** to **`{var}`** inside quoted strings and G-code (no filters).
- Flag **`{{ expr | filter }}`** for manual conversion (cannot auto-fix safely).
- Expand single-line `{% if %}{% set %}{% endif %}` to 3-line form.

Everything else stays read-only to avoid breaking logic.

## CI
Add to your pipeline:
```bash
python3 tools/klipper_macro_lint.py --paths printer.cfg macros/ --config .klipperlint.toml
```

