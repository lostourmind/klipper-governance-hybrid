#!/usr/bin/env python3
import argparse, sys, re, os, pathlib

# Safe, mechanical rewrites only.
RE_MULTI_INLINE = re.compile(r"\{\%([^%]*)(if|for)[^%]*\%\}\s*\{\%\s*set[^%]*\%\}\s*\{\%\s*end\2\s*\%\}")
RE_DOUBLE_MUSTACHE_VAR = re.compile(r"(\")([^\"\n{]*)\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}([^\"\n}]*)\"")

def expand_inline_blocks(text):
    # Heuristic: split one-liners into multi-line blocks
    text = re.sub(r"\{\%\s*if\s+([^%]+)\s*\%\}\s*\{\%\s*set\s+([^%]+)\s*\%\}\s*\{\%\s*endif\s*\%\}",
                  r"{% if \1 %}\n  {% set \2 %}\n{% endif %}", text)
    text = re.sub(r"\{\%\s*for\s+([^%]+)\s*\%\}\s*(.*?)\s*\{\%\s*endfor\s*\%\}",
                  r"{% for \1 %}\n  \2\n{% endfor %}", text)
    return text

def convert_double_mustache_to_single(text):
    # Only convert {{ var }} inside a single quoted string and without filters
    def repl(m):
        # reconstruct safely with {var}
        pre = m.group(1); inner_pre = m.group(2); var = m.group(3); inner_post = m.group(4)
        return f"{pre}{inner_pre}{{{var}}}{inner_post}\""
    return RE_DOUBLE_MUSTACHE_VAR.sub(repl, text)

def main():
    ap = argparse.ArgumentParser(description="Safe auto-fixer for simple Klipper macro issues")
    ap.add_argument("--paths", nargs="+", default=["printer.cfg"], help="Files or globs to modify in-place")
    args = ap.parse_args()

    import glob
    files = []
    for p in args.paths:
        files.extend(glob.glob(p, recursive=True))
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        print("No files found.", file=sys.stderr); return 2

    for f in files:
        try:
            s = open(f,"r",encoding="utf-8",errors="ignore").read()
        except Exception as e:
            print(f"[ERROR] {f}: {e}", file=sys.stderr); continue
        orig = s
        s = expand_inline_blocks(s)
        s = convert_double_mustache_to_single(s)
        if s != orig:
            open(f,"w",encoding="utf-8").write(s)
            print(f"Fixed: {f}")
        else:
            print(f"No changes: {f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
