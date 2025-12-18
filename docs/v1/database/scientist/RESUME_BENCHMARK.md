# How to Stop and Resume MTEB Benchmark

## Stop the Current Benchmark

**Option 1: Use the stop script (recommended)**
```bash
cd docs/v1/database/scientist
./stop_benchmark.sh
```

**Option 2: Manual stop**
```bash
# Find the PID
cat docs/v1/database/scientist/mteb-modernbert.pid

# Stop gracefully (saves current progress)
kill -TERM <PID>

# If needed, force stop
kill -KILL <PID>
```

## Resume the Benchmark

The script automatically saves progress after each task. To resume:

```bash
cd docs/v1/database/scientist
hatch run python run_mteb_modernbert.py --full --resume
```

Or with nohup:
```bash
cd docs/v1/database/scientist
./run_mteb_modernbert.sh --full --resume
```

## How Resume Works

1. **Loads existing results**: Reads `mteb-modernbert-embed-base-results.json`
2. **Identifies completed tasks**: Checks which tasks have results (no errors)
3. **Skips completed tasks**: Only runs tasks that haven't been completed
4. **Uses MTEB cache**: Leverages MTEB's built-in caching (`overwrite_strategy="only-missing"`)
5. **Saves incrementally**: Updates results file after each task

## What Gets Saved

The results file is updated after **each task completion**, so you can safely stop at any time:
- Completed tasks are saved immediately
- Partial progress is preserved
- Failed tasks are marked with errors
- Timeout information is recorded

## Example Workflow

```bash
# Day 1: Start benchmark
./run_mteb_modernbert.sh --full

# Day 1: Stop for the night
./stop_benchmark.sh

# Day 2: Resume (skips 9 completed tasks)
./run_mteb_modernbert.sh --full --resume

# Day 2: Stop again
./stop_benchmark.sh

# Day 3: Resume again (continues from where it left off)
./run_mteb_modernbert.sh --full --resume
```

## Verification

Check progress:
```bash
# View completed tasks
cat docs/v1/database/scientist/mteb-modernbert-embed-base-results.json | python3 -m json.tool | grep -A 2 "tasks_completed"

# View last updated time
cat docs/v1/database/scientist/mteb-modernbert-embed-base-results.json | python3 -m json.tool | grep "last_updated"
```

## Notes

- **MTEB Cache**: Results are also cached in `~/.cache/mteb` by MTEB itself
- **Task Matching**: Tasks are matched by name (e.g., "CQADupstackAndroidRetrieval")
- **Safe to Interrupt**: You can stop/resume as many times as needed
- **No Data Loss**: Each task result is saved immediately after completion

