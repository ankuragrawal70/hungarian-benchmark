#!/bin/bash
# Quick run script for Hungarian Algorithm Benchmark

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   Hungarian Algorithm Performance Benchmark                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Clean previous results
echo "🧹 Cleaning previous results..."
docker-compose down 2>/dev/null || true

# Clean local results directory
rm -rf results/*.json 2>/dev/null || true
rm -rf results/*.md 2>/dev/null || true
rm -rf results/*.html 2>/dev/null || true
rm -rf results/*.txt 2>/dev/null || true
rm -rf results/*.log 2>/dev/null || true
mkdir -p results

echo ""
echo "🏗️  Building Docker images..."
docker-compose build

# Define test scenarios (no JSON files needed!)
SCENARIOS=(
  "small 10 20"
  "medium 50 100"
  "large 100 200"
  "xlarge 250 500"
  "xxlarge 500 1000"
)

echo ""
echo "🐍 Running Python (scipy) benchmarks..."
for scenario in "${SCENARIOS[@]}"; do
  read -r name ops tasks <<< "$scenario"
  echo ''
  echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
  echo "Running $name (${ops}×${tasks}) - SEQUENTIAL (1 core)"
  docker-compose run --rm python python main.py "$name" "$ops" "$tasks" 1
  
  echo ''
  echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
  echo "Running $name (${ops}×${tasks}) - PARALLEL (8 cores)"
  docker-compose run --rm python python main.py "$name" "$ops" "$tasks" 8
done
echo "✅ Python benchmarks completed"

echo ""
echo "🔷 Running Golang benchmarks..."
for scenario in "${SCENARIOS[@]}"; do
  read -r name ops tasks <<< "$scenario"
  echo ''
  echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
  echo "Running $name (${ops}×${tasks}) - SEQUENTIAL (1 core)"
  docker-compose run --rm golang /app/hungarian-benchmark "$name" "$ops" "$tasks" 1
  
  echo ''
  echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
  echo "Running $name (${ops}×${tasks}) - PARALLEL (8 cores)"
  docker-compose run --rm golang /app/hungarian-benchmark "$name" "$ops" "$tasks" 8
done
echo "✅ Golang benchmarks completed"

echo ""
echo "🦀 Running Rust benchmarks..."
for scenario in "${SCENARIOS[@]}"; do
  read -r name ops tasks <<< "$scenario"
  echo ''
  echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
  echo "Running $name (${ops}×${tasks}) - SEQUENTIAL (1 core)"
  docker-compose run --rm rust /app/hungarian-benchmark "$name" "$ops" "$tasks" 1 2>&1
  
  echo ''
  echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
  echo "Running $name (${ops}×${tasks}) - PARALLEL (8 cores)"
  docker-compose run --rm rust /app/hungarian-benchmark "$name" "$ops" "$tasks" 8
done
echo "✅ Rust benchmarks completed"

echo ""
echo "📊 Generating comparison report..."
docker-compose run --rm reporter python compare_results.py

echo ""
echo "📦 Copying final results and report to local folder..."
copy_results
echo "✅ All results copied to ./results/"

echo ""
echo "✅ Benchmark complete!"
echo ""
echo "� Generating comparison reports..."
docker-compose run --rm reporter python compare_results.py

echo ""
echo "✅ All benchmarks complete!"
echo ""
echo "📄 Available reports:"
ls -lh results/
echo ""
echo "View comparison report:"
echo "   cat results/comparison_report.md"
echo ""
