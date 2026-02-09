#!/bin/bash
# Run specific scenario benchmarks

SCENARIO=${1:-"medium"}

echo "Running benchmark for scenario: $SCENARIO"
echo ""

# Generate test data if not exists
if [ ! -f "/testdata/matrix_${SCENARIO}.json" ]; then
  echo "Generating test data for $SCENARIO..."
  docker-compose run --rm generator python generate_testdata.py
fi

# Run Python
echo "Running Python benchmark..."
docker-compose run --rm python python main.py /testdata/matrix_${SCENARIO}.json

echo ""

# Run Golang
echo "Running Golang benchmark..."
docker-compose run --rm golang /app/hungarian-benchmark /testdata/matrix_${SCENARIO}.json

echo ""

# Run Rust
echo "Running Rust benchmark..."
docker-compose run --rm rust /app/hungarian-benchmark /testdata/matrix_${SCENARIO}.json

echo ""

# Show results
echo "Results:"
docker-compose run --rm reporter python compare_results.py
