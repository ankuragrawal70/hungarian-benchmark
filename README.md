# Hungarian Algorithm Performance Benchmark

Cross-language performance comparison of the Hungarian algorithm (linear sum assignment problem) across different programming languages and implementations.

## Overview

This project benchmarks the Hungarian algorithm performance across:
- **Python** (scipy.optimize.linear_sum_assignment)
- **Golang** (munkres-go library)
- **Rust** (pathfinding::kuhn_munkres)
- **Java** (Hungarian Algorithm implementation) - Coming soon
- **JavaScript/Node.js** (munkres-js library) - Coming soon

## Use Case

For the OGA (Operator Guidance Application) system that runs allocation every 2 seconds, this benchmark helps determine:
- Which language provides best performance for real-time allocation
- Scalability with increasing operator/task counts
- Memory usage comparison
- Trade-offs between development speed and runtime performance

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
├── docker-compose.yml
├── results/                    # Benchmark results (auto-generated)
├── testdata/                   # Generated test matrices
├── golang/                     # Go implementation
│   ├── Dockerfile
│   ├── go.mod
│   ├── go.sum
│   ├── main.go
│   └── benchmark.go
├── python/                     # Python implementation
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── benchmark.py
├── java/                       # Java implementation
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/
├── javascript/                 # Node.js implementation
│   ├── Dockerfile
│   ├── package.json
│   └── benchmark.js
└── runner/                     # Orchestrator
    ├── Dockerfile
    ├── requirements.txt
    ├── generate_testdata.py
    ├── run_benchmarks.py
    └── compare_results.py
```

## Quick Start

### Run All Benchmarks
```bash
docker-compose up --build
```

### Run Specific Language
```bash
docker-compose up golang
docker-compose up python
```

### Generate Test Data Only
```bash
docker-compose run runner python generate_testdata.py
```

### View Results
```bash
cat results/comparison_report.md
```

## Benchmark Metrics

For each test scenario and language, we measure:
- **Execution Time**: Time to solve assignment (microseconds)
- **Memory Usage**: Peak memory consumption (MB)
- **Solution Cost**: Total cost of optimal assignment
- **Iterations**: Number of algorithm iterations (if available)

## Expected Results

Based on typical performance characteristics:

| Language | Speed | Memory | Development | Library Quality |
|-Rust | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Golang | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Python (scipy) | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Golang | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Java | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| JavaScript | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

## Output Example

```
╔═══════════════════════════════════════════════════════════════════════╗
║          Hungarian Algorithm Performance Benchmark Results            ║
╚═══════════════════════════════════════════════════════════════════════╝

Test Scenario: Medium (50×100)
─────────────────────────────────────────────────────────────────────────

Language        Execution Time    Memory (MB)    Speedup    Solution Cost
────────────────────────────────────────────────────────────────────────
Rust                1.8 ms           6.3          6.94x        1,245.67
Golang              2.3 ms           8.1          5.43x        1,245.67
Python (scipy)      12.5 ms          45.2         1.00x        1,245.67
Java                4.1 ms          52.3          3.05x        1,245.67
JavaScript         28.7 ms          68.9          0.44x        1,245.67

Winner: Rust (6.94x faster than baseline)
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
