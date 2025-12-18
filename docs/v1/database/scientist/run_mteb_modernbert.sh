#!/bin/bash
# Run MTEB benchmark for modernbert-embed-base with nohup
# This allows the benchmark to run in the background and survive terminal disconnection

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Change to script directory for output files
cd "$SCRIPT_DIR"

# Set up output files
LOG_FILE="mteb-modernbert.log"
OUTPUT_FILE="mteb-modernbert-embed-base-results.json"
NOHUP_OUT="nohup-mteb-modernbert.out"
NOHUP_ERR="nohup-mteb-modernbert.err"

# Parse arguments (pass through to Python script)
ARGS="$@"

# Print start information
echo "=========================================="
echo "Starting MTEB benchmark for modernbert-embed-base"
echo "=========================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Check if --full flag is set
if echo "$ARGS" | grep -q "\--full"; then
    echo "⚠️  FULL BENCHMARK MODE"
    echo "   This will run ALL retrieval tasks (361+ tasks)"
    echo "   This may take many hours to complete!"
    echo ""
elif echo "$ARGS" | grep -q "\--test"; then
    echo "✅ TEST MODE (10 tasks, with timeouts)"
    echo ""
else
    echo "ℹ️  Defaulting to TEST MODE (10 tasks)"
    echo "   Use --full for complete benchmark"
    echo "   Use --test to explicitly set test mode"
    echo ""
fi

echo "Output files:"
echo "  - Results JSON: $OUTPUT_FILE"
echo "  - Script log: $LOG_FILE"
echo "  - Nohup stdout: $NOHUP_OUT"
echo "  - Nohup stderr: $NOHUP_ERR"
echo ""
echo "To monitor progress:"
echo "  tail -f $SCRIPT_DIR/$LOG_FILE"
echo "  tail -f $SCRIPT_DIR/$NOHUP_OUT"
echo ""
echo "To check if still running:"
echo "  ps aux | grep run_mteb_modernbert"
echo ""
echo "Starting benchmark in background..."
echo ""

# Run with nohup using hatch run
# Change to project root for hatch, then run script with relative path
cd "$PROJECT_ROOT"
nohup hatch run python "$SCRIPT_DIR/run_mteb_modernbert.py" $ARGS > "$SCRIPT_DIR/$NOHUP_OUT" 2> "$SCRIPT_DIR/$NOHUP_ERR" &

# Get the process ID
PID=$!

# Save PID to file for easy tracking
echo $PID > "$SCRIPT_DIR/mteb-modernbert.pid"

echo "✅ Benchmark started in background"
echo "   Process ID: $PID"
echo "   PID saved to: mteb-modernbert.pid"
echo ""
echo "Monitor progress with:"
echo "  tail -f $SCRIPT_DIR/$LOG_FILE"
echo ""
echo "To stop the benchmark:"
echo "  kill $PID"
echo ""

