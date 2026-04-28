#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Monitor Training in Real-Time
# ═══════════════════════════════════════════════════════════════════════
#
# Runs a split-view of:
#   - nvidia-smi (GPU utilization + temps)
#   - latest training log (tail -f)
#
# Requires: tmux (install with: sudo apt install tmux)
#
# Alternatively, just use W&B dashboard for richer metrics.

set -e

cd "$(dirname "$0")/.."

if ! command -v tmux &> /dev/null; then
    echo "tmux not installed. Using fallback..."
    echo ""
    echo "GPU status (updates every 2s, Ctrl-C to stop):"
    exec watch -n 2 nvidia-smi
fi

LATEST_LOG=$(ls -t logs/train_*.log 2>/dev/null | head -1)
if [ -z "$LATEST_LOG" ]; then
    echo "No training logs found in logs/. Starting nvidia-smi watch only."
    exec watch -n 2 nvidia-smi
fi

SESSION="advisorai-monitor"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -x 200 -y 50

# Left: GPU monitor
tmux send-keys -t "$SESSION:0.0" "watch -n 2 nvidia-smi" C-m

# Right: tail training log
tmux split-window -h -t "$SESSION:0"
tmux send-keys -t "$SESSION:0.1" "tail -f $LATEST_LOG" C-m

tmux attach -t "$SESSION"
