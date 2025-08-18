# Klipper Governance – Hybrid Setup

Generated: 2025-08-18 21:44

This repo is split so that **configs** live under Git (for rollback), while **governance docs** can be mirrored to Drive/Dropbox for easy review.

## Folders
- `configs/` — your live Klipper configs (Git source of truth)
  - `printer.cfg` — your baseline; replace with your backup
  - `includes/governance_macros.canary.cfg` — only the *one* macro under test
  - `includes/governance_macros.promoted.cfg` — the validated macros after *promote*
- `tools/` — small helper scripts (checkpoint, preflight scan)
- `governance/` — the governance framework & agent docs (also store in Drive)

## First-time Setup
```bash
cd klipper-governance-hybrid
git init
git add .
git commit -m "repo scaffold"
# Put your backed-up printer.cfg into configs/printer.cfg, then:
git add configs/printer.cfg
git commit -m "baseline: printer.cfg"
git tag v1.0-baseline
```

## Canary-first Workflow
1. Put **one** macro under test into `configs/includes/governance_macros.canary.cfg`.
2. In `configs/printer.cfg`, add:
   ```
   [include includes/governance_macros.canary.cfg]
   ```
3. Run a checkpoint and a preflight scan:
   ```bash
   tools/scripts/create_checkpoint.sh
   python3 tools/scripts/run_preflight_scan.py configs
   ```
4. Restart Klipper → if clean, run macro once.
5. If green, **promote**: move the macro into `configs/includes/governance_macros.promoted.cfg`, keep canary empty.
6. Commit & tag:
   ```bash
   git add -A
   git commit -m "promote: <macro> validated"
   git tag v1.1-<macro>-promoted
   ```

## Mass-Edit Gate
- After a green canary, propose global edits via PR or show diffs in the commit.
- Do not touch `printer.cfg` macros globally without a canary that passed.
- Always run preflight before commit.

## Rollback
```bash
git checkout v1.0-baseline   # instant rollback to baseline
# or, restore the last checkpoint:
cp configs/.checkpoints/$(ls -t configs/.checkpoints | head -n1) configs/printer.cfg
```

## RESPOND Discipline (hard rules)
- Use only `RESPOND MSG="..."`.
- Never put `;` inside the message (it starts a comment).
- Avoid square brackets `[]`; prefer `()` or `-`.
- Indent under `gcode:`.
- Use either `RESPOND` **or** `M118`, not both (default: RESPOND only).

