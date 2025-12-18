# Stop and Resume MTEB Benchmark Guide

## Quick Commands

### Stop the Benchmark
```bash
cd docs/v1/database/scientist
./stop_benchmark.sh
```

### Resume the Benchmark
```bash
cd docs/v1/database/scientist
./run_mteb_modernbert.sh --full --resume
```

Or directly:
```bash
cd docs/v1/database/scientist
hatch run python run_mteb_modernbert.py --full --resume
```

## How It Works

### Resume Functionality

The resume feature uses **two layers of protection**:

1. **Results File Check**: Reads `mteb-modernbert-embed-base-results.json` to find completed tasks
2. **MTEB Cache Check**: Uses MTEB's built-in cache (`~/.cache/mteb`) with `overwrite_strategy="only-missing"`
3. **Skips Completed Tasks**: Only runs tasks that haven't been completed (checked in both places)
4. **Saves Incrementally**: Updates results file after **each task** (not just at the end)

**Important**: Even if the results file is incomplete or from a previous run, MTEB's cache will prevent re-running completed tasks. The `overwrite_strategy="only-missing"` parameter tells MTEB to skip any tasks already in its cache.

### Task Matching

Tasks are matched by name extracted from:
- Task metadata (e.g., "CQADupstackAndroidRetrieval")
- Task class name (fallback)
- Task index (last resort)

MTEB's cache system (`~/.cache/mteb`) also helps ensure tasks aren't re-run unnecessarily.

## Current Status

Based on the logs:
- **9 tasks completed** (all CQADupstack series)
- **Currently running**: Task 10 (CQADupstackUnixRetrieval) - large corpus, will take ~13+ days
- **Total remaining**: ~352 tasks

## Stop the Current Run

The benchmark is currently running. To stop it:

```bash
cd docs/v1/database/scientist
./stop_benchmark.sh
```

This will:
1. Send SIGTERM for graceful shutdown (saves current progress)
2. Wait 5 seconds
3. If still running, send SIGKILL
4. Remove PID file

**Note**: The script saves progress after each task, so stopping is safe - no data loss.

## Resume After Stopping

After stopping, resume with:

```bash
cd docs/v1/database/scientist
./run_mteb_modernbert.sh --full --resume
```

The script will:
- Load existing results
- Skip the 9 completed tasks
- Continue from task 10 (or wherever it left off)
- Use MTEB cache to avoid re-running cached tasks

## Verification

Check what's been completed:
```bash
# View results file
cat docs/v1/database/scientist/mteb-modernbert-embed-base-results.json | python3 -m json.tool

# Count completed tasks
grep -c "✓ Finished evaluation" docs/v1/database/scientist/mteb-modernbert.log
```

## Important Notes

1. **Incremental Saves**: Results are saved after **each task**, so stopping is always safe
2. **MTEB Cache**: MTEB also caches in `~/.cache/mteb` - this helps with resume
3. **Task Names**: Tasks are identified by their metadata name (e.g., "CQADupstackAndroidRetrieval")
4. **No Data Loss**: Each completed task is immediately saved to the results file

## Example Workflow

```bash
# Day 1: Start
./run_mteb_modernbert.sh --full

# Day 1: Stop for the night (after 9 tasks complete)
./stop_benchmark.sh

# Day 2: Resume (skips 9 tasks, continues from task 10)
./run_mteb_modernbert.sh --full --resume

# Day 2: Stop again
./stop_benchmark.sh

# Day 3: Resume again
./run_mteb_modernbert.sh --full --resume
```

## Troubleshooting

### If resume doesn't skip tasks

Check the results file format:
```bash
cat mteb-modernbert-embed-base-results.json | python3 -m json.tool | head -50
```

The script looks for tasks with `"result"` key and no `"error"` key.

### If process won't stop

```bash
# Find the process
ps aux | grep run_mteb_modernbert

# Kill manually
kill -TERM <PID>
# Or force kill
kill -KILL <PID>
```

### Check MTEB cache

MTEB caches results in:
```bash
ls -lh ~/.cache/mteb/
```

This cache helps MTEB skip already-completed tasks even if our results file doesn't match exactly.

