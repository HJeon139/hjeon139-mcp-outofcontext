#!/bin/bash
# Stop the running MTEB benchmark gracefully

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/mteb-modernbert.pid"
SCRIPT_NAME="run_mteb_modernbert.py"

# Find running processes
FOUND_PIDS=$(ps aux | grep "$SCRIPT_NAME" | grep -v grep | awk '{print $2}')

if [ -f "$PID_FILE" ]; then
    PID_FROM_FILE=$(cat "$PID_FILE")
    if ps -p "$PID_FROM_FILE" > /dev/null 2>&1; then
        FOUND_PIDS="$PID_FROM_FILE $FOUND_PIDS"
    fi
fi

# Remove duplicates and check
FOUND_PIDS=$(echo $FOUND_PIDS | tr ' ' '\n' | sort -u | tr '\n' ' ')

if [ -z "$FOUND_PIDS" ]; then
    echo "⚠️  No running benchmark process found"
    if [ -f "$PID_FILE" ]; then
        echo "   Removing stale PID file..."
        rm "$PID_FILE"
    fi
    exit 0
fi

echo "Found benchmark process(es): $FOUND_PIDS"
echo "Stopping benchmark..."
echo ""

# Stop all found processes
for PID in $FOUND_PIDS; do
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "  Stopping PID $PID..."
        # Send SIGTERM for graceful shutdown
        kill -TERM "$PID" 2>/dev/null
    fi
done

# Wait for graceful shutdown
sleep 5

# Check if any are still running and force kill if needed
for PID in $FOUND_PIDS; do
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "  ⚠️  PID $PID still running, force killing..."
        kill -KILL "$PID" 2>/dev/null
        sleep 2
    fi
done

# Verify all stopped
STILL_RUNNING=""
for PID in $FOUND_PIDS; do
    if ps -p "$PID" > /dev/null 2>&1; then
        STILL_RUNNING="$STILL_RUNNING $PID"
    fi
done

if [ -n "$STILL_RUNNING" ]; then
    echo "❌ Failed to stop processes: $STILL_RUNNING"
    exit 1
else
    echo "✅ Benchmark stopped successfully"
    if [ -f "$PID_FILE" ]; then
        rm "$PID_FILE"
    fi
    echo ""
    echo "To resume later, run:"
    echo "  cd $SCRIPT_DIR"
    echo "  ./run_mteb_modernbert.sh --full --resume"
fi

