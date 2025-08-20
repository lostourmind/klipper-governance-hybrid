#!/usr/bin/env python3
import argparse, sys, re, os, pathlib, tomllib

RULES = [
    # (priority, code, description, pattern, opts)
    # P0: Syntax Guards
    (0, "double_mustache_forbidden", "Klipper uses single-brace {var}, never {{ var }}.", re.compile(r"\{\{"), {}),
    (0, "pipe_in_single_brace", "Pipes '|' are forbidden inside single-brace injections { ... }.", re.compile(r"\{[^{}\n]*\|[^{}\n]*\}"), {}),
    (0, "inline_control_blocks", "Inline control blocks must be split across lines.", re.compile(r"\{\%[^%]*\%\}[ \t]*\{\%[^%]*\%\}"), {}),
    (0, "flow_control_keywords", "Jinja flow-control not supported (return/break/continue).", re.compile(r"\{\%\s*(return|break|continue)\b"), {}),
    # P1: Klipper-Compat
    (1, "filter_in_mustache_expr", "Filters must be precomputed with {% set ... %}; no filters in { ... }.", re.compile(r"\{[^{}\n]*\|[^{}\n]*\}"), {}),
    (1, "non_ascii", "Non-ASCII characters are not allowed.", re.compile(r"[^\x00-\x7F]"), {"toggle":"strict_ascii"}),
    (1, "m118_usage", "M118 present; prefer RESPOND (enable with allow_m118).", re.compile(r"^\s*M118\b", re.M), {"toggle":"allow_m118", "negate":True}),
    # P2: Governance Hygiene
    (2, "save_config_below_marker", "Content detected below SAVE_CONFIG marker.", re.compile(r"(?is)^\s*#.*?SAVE_CONFIG.*?$\s*(?:.+)$"), {}),
    (2, "respond_semicolon", "Semicolons inside RESPOND messages are not allowed.", re.compile(r"RESPOND\s+MSG\s*=\s*\"[^\"\n]*;[^\"\n]*\""), {}),
    (2, "respond_square_brackets", "Square brackets in RESPOND messages are not allowed.", re.compile(r"RESPOND\s+MSG\s*=\s*\"[^\"\n]*\[[^\"\n]*\][^\"\n]*\""), {}),
    # P3: Style
    (3, "filter_spacing", "Add spaces around filter pipes for readability (style).", re.compile(r"\|\s*(round|int|float)\s*\("), {}),
]

HINTS = {
    "double_mustache_forbidden": "Replace '{{ var }}' with '{var}' and precompute expressions via '{% set var = ... %}'.",
    "pipe_in_single_brace": "Move filters out of '{ ... }': '{% set x_r2 = round(x,2) %}' then use '{x_r2}'.",
    "inline_control_blocks": "Expand to multi-line:\n  {% if cond %}\n    {% set x = ... %}\n  {% endif %}",
    "flow_control_keywords": "Klipper does not support '{% return %}', 'break', 'continue'. Use flags and RESPOND + conditional blocks.",
    "filter_in_mustache_expr": "Precompute filtered values with '{% set ... %}' and only inject simple '{var}'.",
    "non_ascii": "Replace non-ASCII glyphs (e.g., ≥ → >=).",
    "m118_usage": "Use RESPOND MSG instead, unless allow_m118=true in .klipperlint.toml.",
    "save_config_below_marker": "Ensure nothing but Klipper auto-content is below the SAVE_CONFIG marker.",
    "respond_semicolon": "Remove ';' from RESPOND messages; it starts a comment and breaks parsing.",
    "respond_square_brackets": "Avoid '[]' inside RESPOND messages; use parentheses or hyphens.",
    "filter_spacing": "Prefer spaces around '|' in Jinja tags (style only).",
}

def load_config(path):
    cfg = {"general":{"strict_ascii":False,"allow_m118":False,"fail_on_warn":False}, "paths":{"globs":["printer.cfg","macros/**.cfg"]}}
    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
            for k in cfg:
                if k in data:
                    cfg[k].update(data[k])
    except FileNotFoundError:
        pass
    return cfg

def collect_paths(globs):
    import glob
    files = []
    for g in globs:
        files.extend(glob.glob(g, recursive=True))
    return sorted(set([f for f in files if os.path.isfile(f)]))

def main():
    ap = argparse.ArgumentParser(description="Klipper Governance Linter (layered)")
    ap.add_argument("--paths", nargs="+", default=["printer.cfg"], help="Files or globs to scan")
    ap.add_argument("--config", default=".klipperlint.toml", help="Path to config file")
    args = ap.parse_args()

    cfg = load_config(args.config)
    files = []
    for p in args.paths:
        files.extend(collect_paths([p]))
    if not files:
        print("No files found.", file=sys.stderr)
        return 2

    had_error = False
    for f in files:
        try:
            txt = open(f, "r", encoding="utf-8", errors="ignore").read()
        except Exception as e:
            print(f"[ERROR] {f}: {e}", file=sys.stderr)
            had_error = True
            continue

        # Accumulate by priority
        buckets = {0:[],1:[],2:[],3:[]}
        for pri, code, desc, pat, opts in RULES:
            toggle = opts.get("toggle")
            negate = opts.get("negate", False)
            # Handle toggles from config
            if toggle:
                flag = bool(cfg["general"].get(toggle, False))
                if negate and flag:
                    # rule disabled because allowed
                    continue
                if not negate and not flag and code=="non_ascii":
                    # by default we only warn unless strict_ascii=true -> promote to error
                    pass
            for m in pat.finditer(txt):
                ln = txt.count("\n", 0, m.start()) + 1
                line = txt.splitlines()[ln-1][:240]
                buckets[pri].append((code, desc, ln, line))

        def emit(pri):
            nonlocal had_error
            if buckets[pri]:
                head = {0:"P0 Syntax Guards",1:"P1 Klipper-Compat",2:"P2 Governance Hygiene",3:"P3 Style"}[pri]
                print(f"\n✗ {f} — {head}")
                for code, desc, ln, line in buckets[pri]:
                    hint = HINTS.get(code,"")
                    print(f"  [{code}] line {ln}: {desc}")
                    if hint:
                        print(f"    hint: {hint}")
                    print(f"    > {line}")
                # Determine failure
                if pri in (0,1,2):
                    had_error = True
                elif pri==3 and cfg["general"].get("fail_on_warn", False):
                    had_error = True

        # Emit in priority order, stopping early only on display, not scanning
        emit(0); emit(1); emit(2); emit(3)

    if had_error:
        print("\nLint failed. Fix violations above.", file=sys.stderr)
        return 1
    print("OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
