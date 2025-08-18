#!/usr/bin/env bash
set -euo pipefail
ts=$(date +"%Y%m%d-%H%M%S")
mkdir -p configs/.checkpoints
cp configs/printer.cfg configs/.checkpoints/printer.cfg.ckpt.$ts
echo "Checkpoint saved: configs/.checkpoints/printer.cfg.ckpt.$ts"
