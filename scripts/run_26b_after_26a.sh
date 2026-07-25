#!/bin/bash
# Watch for 26A to finish, then launch 26B automatically (so both arms complete overnight).
#
# 26A is already running in another terminal. This script polls 26A's per-arm ledger and starts
# 26B ONLY after 26A writes a 'stopped'/'complete' row (i.e. it genuinely reached step 12000).
# A mere 'paused' row (Ctrl-C) will NOT trigger it, so pausing/resuming 26A is safe.
#
# Run in a SECOND terminal, in the repo root, with the SAME env as 26A (.venv312):
#   source .venv312/bin/activate
#   caffeinate -dimsu bash scripts/run_26b_after_26a.sh
# (caffeinate keeps the Mac awake; keep the external drive connected.)

set -u
cd "$(dirname "$0")/.."   # repo root

LEDGER="outputs/checkpoints/pants-level45/exp26A_lam0/run_ledger.csv"
LOG="outputs/exp26B_autostart.log"

echo "[watch $(date '+%H:%M:%S')] waiting for 26A to finish -> $LEDGER" | tee -a "$LOG"

while true; do
  # a completed 26A leaves a row whose status column is 'stopped' or 'complete'
  if [ -f "$LEDGER" ] && grep -E "exp26A_lam0," "$LEDGER" | grep -Eq ",(stopped|complete),"; then
    echo "[watch $(date '+%H:%M:%S')] 26A finished. launching 26B..." | tee -a "$LOG"
    break
  fi
  sleep 60
done

python scripts/train.py --label-mode anatomy5 --whole-box --crop-native 16 --patch 128 \
  --init-weights outputs/checkpoints/exp26_init_5ch.pt \
  --train-ids configs/cohorts/exp26/train.txt --val-ids configs/cohorts/exp26/val20.txt \
  --report-ids configs/cohorts/exp26/report40.txt --neg-ids configs/cohorts/exp26/report40_neg.txt \
  --lambda-anat 0.3 --max-iters 24000 --stop-after-step 12000 --val-every 500 --cache disk \
  --run-name exp26B_lam03 2>&1 | tee -a "$LOG"

echo "[watch $(date '+%H:%M:%S')] 26B run exited. check $LOG" | tee -a "$LOG"
