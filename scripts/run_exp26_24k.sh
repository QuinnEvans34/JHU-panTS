#!/bin/bash
# Continue BOTH EXP-26 arms from their 12k checkpoints to the full 24k horizon, back-to-back.
# 26A runs first; 26B starts ONLY if 26A actually completed (reached step 24000), so a Ctrl-C
# pause of 26A will not prematurely kick off 26B.
#
# Run in the repo root, SAME env as training (.venv312), lid open + drive connected:
#   source .venv312/bin/activate
#   caffeinate -dimsu bash scripts/run_exp26_24k.sh
# (caffeinate blocks idle sleep; closing the lid still sleeps the Mac unless in clamshell mode —
#  if it sleeps, the run suspends and resumes on wake; if the drive dropped, just re-run this script,
#  each arm will --resume from its own last.pt with no meaningful loss.)

cd "$(dirname "$0")/.."   # repo root
LOG="outputs/exp26_24k.log"
CKPT=outputs/checkpoints/pants-level45

common=(--label-mode anatomy5 --whole-box --crop-native 16 --patch 128
        --init-weights outputs/checkpoints/exp26_init_5ch.pt
        --train-ids configs/cohorts/exp26/train.txt --val-ids configs/cohorts/exp26/val20.txt
        --report-ids configs/cohorts/exp26/report40.txt --neg-ids configs/cohorts/exp26/report40_neg.txt
        --max-iters 24000 --val-every 500 --cache disk)

echo "[24k $(date '+%H:%M:%S')] resuming 26A -> 24000" | tee -a "$LOG"
python scripts/train.py "${common[@]}" --lambda-anat 0.0 --run-name exp26A_lam0 \
  --resume "$CKPT/exp26A_lam0/last.pt" 2>&1 | tee -a "$LOG"

# only proceed to 26B if 26A reached 24000 (a 'complete' ledger row; a 12k run wrote 'stopped')
if grep -q ",complete," "$CKPT/exp26A_lam0/run_ledger.csv"; then
  echo "[24k $(date '+%H:%M:%S')] 26A complete. resuming 26B -> 24000" | tee -a "$LOG"
  python scripts/train.py "${common[@]}" --lambda-anat 0.3 --run-name exp26B_lam03 \
    --resume "$CKPT/exp26B_lam03/last.pt" 2>&1 | tee -a "$LOG"
  echo "[24k $(date '+%H:%M:%S')] both arms at 24000. run the report40 evals + paired_bootstrap." | tee -a "$LOG"
else
  echo "[24k $(date '+%H:%M:%S')] 26A did NOT complete (paused?). NOT starting 26B. Re-run this script to continue." | tee -a "$LOG"
fi
