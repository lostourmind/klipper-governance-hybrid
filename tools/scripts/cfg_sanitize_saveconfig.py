#!/usr/bin/env python3
import re, sys, pathlib, datetime

MARKER = r"#\*#\s*<---------------------- SAVE_CONFIG ---------------------->"
AUTO_START_RE = re.compile(MARKER)
AUTO_HEADER_RE = re.compile(r"^#\*#\s*DO NOT EDIT THIS BLOCK OR BELOW\.", re.M)

SECTION_RE = re.compile(r"(?ms)^\[([a-zA-Z0-9_]+)(?:\s+[^\]]+)?\].*?(?=^\[[^\]]+\]|\Z)")
MACRO_RE = re.compile(r"(?ms)^\[gcode_macro\s+[^\]]+\].*?(?=^\[[^\]]+\]|\Z)")

def split_auto_blocks(text):
    blocks = list(AUTO_START_RE.finditer(text))
    if not blocks:
        return text, "", []
    # Keep everything before the FIRST marker as head, collect auto parts from first to end
    first = blocks[0].start()
    head = text[:first].rstrip() + "\n"
    tail = text[first:]
    return head, tail, blocks

def extract_macros(text):
    return list(MACRO_RE.finditer(text))

def dedupe_sections(head):
    seen = set()
    out = []
    report = []
    pos = 0
    for m in SECTION_RE.finditer(head):
        start, end = m.span()
        if start > pos:
            out.append(head[pos:start])
        header = m.group(0)
        name = m.group(1).strip().lower()
        if name in seen:
            # comment out duplicate block
            commented = "\n".join("# DUPLICATE REMOVED: " + ln for ln in header.splitlines())
            out.append(commented + "\n")
            report.append(f"Duplicate section [{name}] commented out.")
        else:
            out.append(header)
            seen.add(name)
        pos = end
    out.append(head[pos:])
    return "".join(out), report

def main(path):
    p = pathlib.Path(path)
    original = p.read_text(encoding="utf-8", errors="ignore")
    head, auto_zone, markers = split_auto_blocks(original)

    # If multiple markers exist, keep only the LAST auto block contents
    if markers:
        # Extract all marker positions in auto_zone
        parts = re.split(MARKER, auto_zone)
        # parts[0] is empty (split includes leading), each subsequent starts with the auto header and auto-generated body
        # Keep only the last marker body
        if len(parts) > 2:
            # Reattach the marker for the last block
            auto_zone = MARKER + parts[-1]
        # Ensure auto header exists
        if not AUTO_HEADER_RE.search(auto_zone):
            auto_zone = MARKER + "\n#*# DO NOT EDIT THIS BLOCK OR BELOW. The contents are auto-generated.\n\n" + auto_zone

    # Pull any gcode_macro blocks that accidentally got written inside auto_zone, and move them to head
    moved = []
    if auto_zone:
        macros = extract_macros(auto_zone)
        # Remove macros from auto_zone and append to head end
        if macros:
            new_auto = auto_zone
            for m in reversed(macros):  # reverse to preserve indices while slicing
                block = m.group(0)
                moved.append(block.splitlines()[0])
                new_auto = new_auto[:m.start()] + new_auto[m.end():]
            head = head.rstrip() + "\n\n# ---- Macros recovered from auto-generated area ----\n" + "\n\n".join(b for b in (mb for mb in (mm.group(0) for mm in macros))) + "\n"
            auto_zone = new_auto

    # De-duplicate sections in head (commenting out later duplicates)
    head_deduped, report = dedupe_sections(head)

    # Stitch final
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final = head_deduped.rstrip() + "\n\n" + auto_zone.lstrip() if auto_zone else head_deduped
    # Write backup
    bak = p.with_suffix(p.suffix + f".preclean.{ts.replace(':','').replace(' ','_')}.bak")
    bak.write_text(original, encoding="utf-8")
    p.write_text(final, encoding="utf-8")

    print("Clean complete. Report:")
    if moved:
        print(" - Moved macros out of SAVE_CONFIG auto area:")
        for m in moved:
            print("   *", m)
    if report:
        print(" - Duplicate sections commented:")
        for r in report:
            print("   *", r)
    if not moved and not report:
        print(" - No issues found.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cfg_sanitize_saveconfig.py /path/to/printer.cfg")
        sys.exit(2)
    main(sys.argv[1])
