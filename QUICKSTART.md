# Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- At least 2GB free disk space
- 4GB+ RAM recommended for large scenarios

## Run All Benchmarks (Recommended)

```bash
cd /Users/ankur.a/g_orange/hungarian-benchmark
./run_benchmark.sh
```

This will:
1. Generate test data for all scenarios (small → xxlarge)
2. Run Python (scipy) benchmarks
3. Run Golang benchmarks
4. Run Rust benchmarks
5. Generate comparison report

## Run Single Scenario

```bash
# Run only medium scenario (50×100)
./run_single.sh medium

# Run large scenario (100×200)
./run_single.sh large
```

## View Results

### Terminal Output
Results are printed during execution with colored output.

### Markdown Report
```bash
docker-compose run --rm reporter cat /results/comparison_report.md
```

### Raw JSON Results
```bash
docker-compose run --rm reporter ls -la /results/
docker-compose run --rm reporter cat /results/python_medium.json
docker-compose run --rm reporter cat /results/golang_medium.json
```

## Manual Steps

### 1. Generate Test Data
```bash
docker-compose run --rm generator python generate_testdata.py
```

### 2. Run Python Benchmark
```bash
docker-compose run --rm python python main.py /testdata/matrix_medium.json
```

### 3. Run Golang Benchmark
```bash
docker-compose run --rm golang /app/hungarian-benchmark /testdata/matrix_medium.json
```

### 4. Run Rust Benchmark
```bash
docker-compose run --rm rust /app/hungarian-benchmark /testdata/matrix_medium.json
```

### 5. Compare Results
```bash
docker-compose run --rm reporter python compare_results.py
```

## Troubleshooting

### Build fails
```bash
docker-compose down -v
docker-compose build --no-cache
```

### Out of memory for large scenarios
Edit docker-compose.yml and add memory limits:
```yaml
services:
  golang:
    mem_limit: 4g
```

### Results not appearing
Check if containers completed successfully:
```bash
docker-compose ps -a
docker-compose logs golang
docker-compose logs python
```

## Customization

### Add Your Own Test Scenario
Edit `runner/generate_testdata.py`:
```python
SCENARIOS = [
    # ... existing scenarios
    {"name": "custom", "operators": 75, "tasks": 150, "description": "Custom scenario"},
]
```

### Adjust Cost Generation
Modify `generate_realistic_cost_matrix()` in `runner/generate_testdata.py` to change:
- Distance ranges
- Zone penalties
- Idle time bonuses

### Change Random Seed
For reproducible results, the seed is set to 42. Change in `generate_testdata.py`:
```python
random.seed(42)  # Change to different number
```

## Expected Performance

Based on typical results:

| Scenario | Python (scipy) | Golang | Rust | Best |
|----------|----------------|--------|------|------|
| Small (10×20) | ~1-2 ms | ~0.3-0.5 ms | ~0.2-0.4 ms | Rust |
| Medium (50×100) | ~10-15 ms | ~2-3 ms | ~1.5-2.5 ms | Rust |
| Large (100×200) | ~50-70 ms | ~8-12 ms | ~6-10 ms | Rust |
| XLarge (250×500) | ~500-700 ms | ~80-120 ms | ~60-100 ms | Rust |
| XXLarge (500×1000) | ~3-5 sec | ~500-800 ms | ~400-700 ms | Rust |

**Note:** Actual performance depends on your hardware.

## Clean Up

Remove all containers, volumes, and images:
```bash
docker-compose down -v
docker system prune -a
```
