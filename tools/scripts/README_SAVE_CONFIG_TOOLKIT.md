# SAVE_CONFIG Hygiene Toolkit

## Why
Klipper appends auto-generated config to the bottom of `printer.cfg` under a SAVE_CONFIG marker.
If macros or includes get written there (by accident or merges), Klipper may ignore saved values or error at startup.

## What this toolkit does
- `cfg_sanitize_saveconfig.py`:
  * Ensures only ONE SAVE_CONFIG block remains (keeps the LAST one)
  * Moves any `[gcode_macro ...]` accidentally placed inside the auto-generated area back above the marker
  * Comments out duplicate `[section]` headers after the first (and reports them)
  * Writes a timestamped `.preclean.*.bak` before modifying your file

- `precommit_saveconfig_guard.sh`:
  * Git pre-commit hook that blocks commits if multiple SAVE_CONFIG markers exist
  * Blocks commits if `[gcode_macro ...]` appears in the auto-generated area

## How to use
1) Make a backup of your `printer.cfg`.
2) Run:
   ```bash
   python cfg_sanitize_saveconfig.py /path/to/printer.cfg
   ```
3) Review the printed report and the updated `printer.cfg`.
4) (Optional) Install the pre-commit hook in your repo:
   ```bash
   cp precommit_saveconfig_guard.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```
