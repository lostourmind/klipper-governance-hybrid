#!/usr/bin/env python3
import sys, re, pathlib

def scan(path):
    errors = []
    for p in pathlib.Path(path).rglob("*.cfg"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        # RESPOND MSG syntax
        for i, ln in enumerate(lines, 1):
            if "RESPOND" in ln:
                if "MSG=" not in ln:
                    errors.append((p, i, "RESPOND without MSG="))
                # semicolon inside quotes
                m = re.search(r'MSG\s*=\s*"([^"]*)"', ln)
                if m and ";" in m.group(1):
                    errors.append((p, i, "Semicolon inside RESPOND MSG (breaks parsing)"))
                if m and ("[" in m.group(1) or "]" in m.group(1)):
                    errors.append((p, i, "Square brackets inside RESPOND MSG (avoid)"))

        # crude Jinja if/endif balance per file
        ifs = sum(1 for ln in lines if "{% if" in ln)
        endifs = sum(1 for ln in lines if "{% endif %}" in ln)
        if ifs != endifs:
            errors.append((p, 0, f"Jinja if/endif imbalance: if={ifs} endif={endifs}"))

        # SAVE_VARIABLE primitive check
        for i, ln in enumerate(lines, 1):
            if "SAVE_VARIABLE" in ln:
                m = re.search(r'VALUE\s*=\s*(.+)$', ln)
                if m:
                    val = m.group(1).strip()
                    if val.startswith('"') or val.startswith("'"):
                        errors.append((p, i, "SAVE_VARIABLE uses string (not allowed)"))
    return errors

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "configs"
    errs = scan(folder)
    if not errs:
        print("Preflight: OK ✅")
        sys.exit(0)
    print("Preflight: issues found ❌")
    for p, i, msg in errs:
        loc = f"{p}:{i}" if i else f"{p}"
        print(f" - {loc}: {msg}")
    sys.exit(1)
