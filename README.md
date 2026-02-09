# Hungarian Algorithm Performance Benchmark

Cross-language performance comparison of the Hungarian algorithm (linear sum assignment problem) across different programming languages and implementations.

## Overview

This project benchmarks the Hungarian algorithm performance across:
- **Python** (scipy.optimize.linear_sum_assignment) with multiprocessing
- **Golang** (oddg/hungarian-algorithm) with goroutines
- **Rust** (pathfinding::kuhn_munkres) with rayon

### Key Features
- **CPU-Heavy Workload**: Simulates realistic cost calculation with 9 weighted factors (100 iterations per cell)
- **Parallel Execution**: Tests both sequential (1 core) and parallel (8 cores) modes
- **No I/O Overhead**: Matrices generated in-memory via CLI arguments (no JSON file loading)
- **Comprehensive Metrics**: 4-category winners (Matrix Gen, Algorithm, Total Time, Memory)
- **Accurate Memory Tracking**: Includes multiprocessing overhead in Python

## Use Case

For the OGA (Operator Guidance Application) system that runs allocation every 2 seconds, this benchmark helps determine:
- Which language provides best overall performance (including cost matrix generation)
- Whether Golang's 9.4ms total time (50×100 parallel) meets the 2-3 second target ✅
- Memory efficiency comparison (Rust: 0 MB, Golang: 1.1 MB, Python: 2.1 MB)
- Parallel scaling benefits (2-3x speedup across all languages)
- Trade-offs between pure algorithm speed vs. complete workload performance

## Test Scenarios

| Scenario | Operators | Tasks | Matrix Size | Use Case |
|----------|-----------|-------|-------------|----------|
| Small | 10 | 20 | 10×20 | Low traffic warehouse |
| Medium | 50 | 100 | 50×100 | Medium warehouse |
| Large | 100 | 200 | 100×200 | High traffic warehouse |
| XLarge | 250 | 500 | 250×500 | Multiple warehouses |
| XXLarge | 500 | 1000 | 500×1000 | Enterprise scale |

## Project Structure

```
hungarian-benchmark/
├── README.md
├── QUICKSTART.md
├── docker-compose.yml          # Docker services configuration
├── run_benchmark.sh            # Main benchmark orchestrator
├── run_single.sh               # Run single scenario
├── results/                    # Benchmark results (bind mounted)
│   ├── python_results.json     # Consolidated Python results
│   ├── golang_results.json     # Consolidated Golang results
│   ├── rust_results.json       # Consolidated Rust results
│   ├── comparison_report.md    # Markdown report
│   ├── comparison_report.html  # HTML report
│   └── comparison_report_confluence.txt  # Confluence markup
├── golang/                     # Go implementation
│   ├── Dockerfile
│   ├── go.mod
│   ├── go.sum
│   └── main.go                 # CLI-based with goroutines
├── python/                     # Python implementation
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                 # CLI-based with multiprocessing
├── rust/                       # Rust implementation
│   ├── Dockerfile
│   ├── Cargo.toml
│   └── src/main.rs             # CLI-based with rayon
└── runner/                     # Report generator
    ├── Dockerfile
    ├── requirements.txt
    ├── compare_results.py      # Generates comparison reports
    └── generate_testdata.py    # (Legacy - not used)
```

## Quick Start

### Run All Benchmarks (Recommended)
```bash
./run_benchmark.sh
```
Runs 30 benchmarks (5 scenarios × 2 modes × 3 languages) and generates reports.

### Run Single Scenario
```bash
# Sequential (1 core)
./run_single.sh medium 50 100 1

# Parallel (8 cores)
./run_single.sh medium 50 100 8
```

### Run Specific Language
```bash
# Python
docker-compose run --rm python python main.py medium 50 100 8

# Golang
docker-compose run --rm golang /app/hungarian-benchmark medium 50 100 8

# Rust
docker-compose run --rm rust /app/hungarian-benchmark medium 50 100 8
```

### View Results
```bash
cat results/comparison_report.md      # Markdown
open results/comparison_report.html   # HTML (in browser)
cat results/python_results.json       # Raw Python data
```

### Clean Results
```bash
rm -rf results/*.json results/*.md results/*.html results/*.txt
```

## Benchmark Metrics

For each test scenario and language, we measure:
- **Matrix Gen Time**: Time to generate cost matrix with CPU-heavy computation (ms)
- **Algorithm Time**: Pure Hungarian algorithm execution time (ms)
- **Total Time**: Matrix Gen + Algorithm (ms) - **primary performance metric**
- **Memory Usage**: Peak memory including multiprocessing overhead (MB)
- **Solution Cost**: Total cost of optimal assignment (for verification)
- **Assignments**: Number of operator-task assignments

### 4-Category Winners
Each scenario reports winners across 4 categories:
1. **📊 Matrix Gen Winner**: Fastest at generating cost matrix
2. **⚡ Algorithm Winner**: Fastest pure Hungarian algorithm
3. **🎯 Total Time Winner**: Best overall performance (**most important**)
4. **💾 Memory Winner**: Most memory-efficient implementation

## Expected Results

Based on actual benchmark results (Medium 50×100 scenario):

### Sequential (1 Core)
| Metric | Python | Golang | Rust | Winner |
|--------|--------|--------|------|--------|
| Matrix Gen | 213.6 ms | 14.3 ms ⭐ | 47.7 ms | Golang (15x faster) |
| Algorithm | 0.048 ms ⭐ | 0.203 ms | 0.057 ms | Python |
| **Total Time** | 213.6 ms | **14.5 ms** ⭐ | 47.7 ms | **Golang (15x faster)** |
| Memory | 0.09 MB | 1.10 MB | 0.00 MB ⭐ | Rust |

### Parallel (8 Cores)
| Metric | Python | Golang | Rust | Winner |
|--------|--------|--------|------|--------|
| Matrix Gen | 66.1 ms | 6.1 ms ⭐ | 16.2 ms | Golang (11x faster) |
| Algorithm | 0.046 ms | 0.184 ms | 0.070 ms ⭐ | Python |
| **Total Time** | 66.2 ms | **6.3 ms** ⭐ | 16.3 ms | **Golang (10x faster)** |
| Memory | 2.14 MB | 1.12 MB | 0.00 MB ⭐ | Rust |

### Key Insights
| Aspect | Rating | Notes |
|--------|--------|-------|
| **Golang - Total Performance** | ⭐⭐⭐⭐⭐ | Fastest overall (6-15x faster than Python) |
| **Rust - Algorithm Speed** | ⭐⭐⭐⭐⭐ | Fastest pure algorithm execution |
| **Rust - Memory Efficiency** | ⭐⭐⭐⭐⭐ | Zero measurable overhead |
| **Python - Development Speed** | ⭐⭐⭐⭐⭐ | Excellent library (scipy), simple code |
| **Golang - Balanced Choice** | ⭐⭐⭐⭐⭐ | Best for production (speed + memory + simplicity) |
| **Parallel Scaling** | ⭐⭐⭐⭐ | 2-3x speedup across all languages |

## Output Example

```
====================================================================================================
  MEDIUM
====================================================================================================

📊 SEQUENTIAL (1 Core)

+----------+--------------------------------+----------+-------------------+-----------+--------------+
| Language | Implementation                 | Matrix   | Matrix Gen (ms)   | Algo (ms) | Total (ms)   |
+==========+================================+==========+===================+===========+==============+
| Golang   | hungarian-algorithm (seq)      | 50x100   | 14.252            | 0.203     | 14.455       |
+----------+--------------------------------+----------+-------------------+-----------+--------------+
| Rust     | pathfinding::kuhn_munkres      | 50x100   | 47.657            | 0.057     | 47.713       |
+----------+--------------------------------+----------+-------------------+-----------+--------------+
| Python   | scipy.optimize (seq)           | 50x100   | 213.583           | 0.048     | 213.631      |
+----------+--------------------------------+----------+-------------------+-----------+--------------+

🏆 Winners (Sequential):
  📊 Matrix Gen: Golang (14.252ms)
  ⚡ Algorithm: Python (0.048ms)
  🎯 Total Time: Golang (14.455ms)
  💾 Memory: Rust (0.00MB)

📊 PARALLEL (8 Cores)

+----------+--------------------------------+----------+-------------------+-----------+--------------+
| Language | Implementation                 | Matrix   | Matrix Gen (ms)   | Algo (ms) | Total (ms)   |
+==========+================================+==========+===================+===========+==============+
| Golang   | hungarian-algorithm (parallel) | 50x100   | 6.111             | 0.184     | 6.295        |
+----------+--------------------------------+----------+-------------------+-----------+--------------+
| Rust     | pathfinding::kuhn_munkres (par)| 50x100   | 16.218            | 0.070     | 16.287       |
+----------+--------------------------------+----------+-------------------+-----------+--------------+
| Python   | scipy.optimize (parallel)      | 50x100   | 66.106            | 0.046     | 66.153       |
+----------+--------------------------------+----------+-------------------+-----------+--------------+

🏆 Winners (Parallel):
  📊 Matrix Gen: Golang (6.111ms)
  ⚡ Algorithm: Python (0.046ms)
  🎯 Total Time: Golang (6.295ms)
  💾 Memory: Rust (0.00MB)
```

## Adding New Languages

To add a new language implementation:

1. Create directory: `<language>/`
2. Implement benchmark following interface:
   - Read matrix from `/testdata/matrix_<size>.json`
   - Run Hungarian algorithm
   - Output results to `/results/<language>_<size>.json`
3. Add Dockerfile
4. Update docker-compose.yml
5. Update comparison script

## License

MIT
