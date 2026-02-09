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
1. Run all 5 test scenarios (small → xxlarge) 
2. Execute each scenario in sequential (1 core) and parallel (8 cores) modes
3. Run Python, Golang, and Rust implementations
4. Generate comprehensive comparison reports
5. Display 4-category winners: Matrix Gen, Algorithm, Total Time, Memory

**Total:** 30 benchmark runs (5 scenarios × 2 modes × 3 languages)

## View Results

### Terminal Output
Results are printed during execution with colored output showing 4 winners per scenario:
- 📊 Matrix Gen: Fastest at generating cost matrix
- ⚡ Algorithm: Fastest Hungarian algorithm execution
- 🎯 Total Time: Best overall performance (Matrix Gen + Algo)
- 💾 Memory: Most memory-efficient

### Markdown Report
```bash
cat results/comparison_report.md
```

### HTML Report (Pretty Formatted)
```bash
open results/comparison_report.html
```

### Raw JSON Results
```bash
ls -la results/
cat results/python_results.json   # All Python results
cat results/golang_results.json   # All Golang results
cat results/rust_results.json     # All Rust results
```

## Manual Steps

### Run Single Benchmark (Manual)
```bash
# Python - Sequential
docker-compose run --rm python python main.py medium 50 100 1

# Python - Parallel (8 cores)
docker-compose run --rm python python main.py medium 50 100 8

# Golang - Sequential
docker-compose run --rm golang /app/hungarian-benchmark medium 50 100 1

# Golang - Parallel (8 cores)
docker-compose run --rm golang /app/hungarian-benchmark medium 50 100 8

# Rust - Sequential
docker-compose run --rm rust /app/hungarian-benchmark medium 50 100 1

# Rust - Parallel (8 cores)
docker-compose run --rm rust /app/hungarian-benchmark medium 50 100 8
```

### Generate Comparison Report
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
Edit `run_benchmark.sh` and add your scenario:
```bash
SCENARIOS=(
    "small:10:20"
    "medium:50:100"
    "large:100:200"
    "xlarge:250:500"
    "xxlarge:500:1000"
    "custom:75:150"  # Add your custom scenario
)
```

### Adjust Cost Generation
Modify the cost calculation in each language implementation:
- `python/main.py` - `generate_operator_row()` function
- `golang/main.go` - `generateOperatorRow()` function
- `rust/src/main.rs` - `generate_operator_row()` function

The cost function simulates 9 weighted factors:
- op_remaining_time_cost, op_reach_time_cost, op_wait_time_cost
- bot_starvation_cost, localized_marker_cost, total_quantity_cost
- zone_distance, zone_full_penalty, idle_penalty

### Change Random Seed
For reproducible results, the seed is based on operator index. Modify in each implementation:
```python
# Python
random.seed(seed + i)  # seed argument passed from CLI
```

## Expected Performance

Based on actual benchmark results (Total Time = Matrix Generation + Algorithm):

### Sequential (1 Core)
| Scenario | Python | Golang | Rust | Total Winner | Algo Winner |
|----------|--------|--------|------|--------------|-------------|
| Small (10×20) | ~25 ms | ~1.7 ms | ~4.7 ms | Golang | Python |
| Medium (50×100) | ~214 ms | ~14.5 ms | ~48 ms | Golang | Python |
| Large (100×200) | ~840 ms | ~55 ms | ~183 ms | Golang | Rust |
| XLarge (250×500) | ~5400 ms | ~350 ms | ~1100 ms | Golang | Rust |
| XXLarge (500×1000) | ~22900 ms | ~1842 ms | ~4295 ms | Golang | Rust |

### Parallel (8 Cores)
| Scenario | Python | Golang | Rust | Total Winner | Algo Winner |
|----------|--------|--------|------|--------------|-------------|
| Small (10×20) | ~15 ms | ~1.1 ms | ~2.1 ms | Golang | Rust |
| Medium (50×100) | ~66 ms | ~6.3 ms | ~16 ms | Golang | Rust |
| Large (100×200) | ~270 ms | ~22 ms | ~47 ms | Golang | Rust |
| XLarge (250×500) | ~1600 ms | ~110 ms | ~280 ms | Golang | Rust |
| XXLarge (500×1000) | ~7158 ms | ~625 ms | ~1128 ms | Golang | Rust |

**Key Insights:**
- **Golang** consistently wins on total time (matrix generation is dominant)
- **Rust** has fastest pure algorithm execution (0.04-2.5ms)
- **Python** shows best parallel scaling but highest overhead
- Parallel execution provides 2-3x speedup for all languages

**Note:** Actual performance depends on your hardware.

## Clean Up

Remove all containers, volumes, and images:
```bash
docker-compose down -v
docker system prune -a
```
