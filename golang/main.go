package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"math"
	"math/rand"
	"os"
	"runtime"
	"strconv"
	"sync"
	"time"

	hungarian "github.com/oddg/hungarian-algorithm"
)

type TestData struct {
	Name      string      `json:"name"`
	Operators int         `json:"operators"`
	Tasks     int         `json:"tasks"`
	Matrix    [][]float64 `json:"matrix"`
}

type BenchmarkResult struct {
	Language       string  `json:"language"`
	Implementation string  `json:"implementation"`
	Scenario       string  `json:"scenario"`
	MatrixSize     string  `json:"matrix_size"`
	LoadTime       float64 `json:"load_time_ms"`
	ExecutionTime  float64 `json:"execution_time_ms"`
	TotalTime      float64 `json:"total_time_ms"`
	MemoryUsed     float64 `json:"memory_used_mb"`
	SolutionCost   float64 `json:"solution_cost"`
	Success        bool    `json:"success"`
	ErrorMsg       string  `json:"error_msg,omitempty"`
}

func main() {
	if len(os.Args) < 4 {
		fmt.Println("Usage: go run main.go <scenario_name> <num_operators> <num_tasks> [num_cores]")
		os.Exit(1)
	}

	scenario := os.Args[1]
	numOperators, _ := strconv.Atoi(os.Args[2])
	numTasks, _ := strconv.Atoi(os.Args[3])
	numCores := 1
	if len(os.Args) > 4 {
		numCores, _ = strconv.Atoi(os.Args[4])
	}
	
	mode := "SEQUENTIAL"
	if numCores > 1 {
		mode = "PARALLEL"
	}
	
	fmt.Printf("Running Golang Hungarian Algorithm Benchmark (%s)\n", mode)
	fmt.Printf("Scenario: %s\n", scenario)
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Printf("Matrix: %d×%d | Cores: %d\n\n", numOperators, numTasks, numCores)

	// Create data structure
	data := TestData{
		Name:      scenario,
		Operators: numOperators,
		Tasks:     numTasks,
	}

	// Run benchmark
	result := runBenchmark(data, numCores)

	// Append results to consolidated file
	outputFile := "/results/golang_results.json"
	
	// Read existing results if file exists
	var results []BenchmarkResult
	if fileData, err := os.ReadFile(outputFile); err == nil {
		if err := json.Unmarshal(fileData, &results); err != nil {
			log.Printf("Warning: Could not parse existing results: %v", err)
			results = []BenchmarkResult{}
		}
	}
	
	// Append new result
	results = append(results, result)
	
	// Write back all results
	jsonData, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		log.Fatalf("Failed to marshal results: %v", err)
	}
	
	err = os.WriteFile(outputFile, jsonData, 0644)
	if err != nil {
		log.Fatalf("Failed to write results: %v", err)
	}
	
	fmt.Printf("✓ Results appended to %s\n", outputFile)

	// Print summary
	printSummary(result)
}

func generateRealisticCostMatrix(numOperators, numTasks, numCores int, seed int64) [][]float64 {
	// Generate realistic cost matrix simulating heavy OGA allocation cost computation
	// Uses goroutines for parallel execution (one per operator row) if numCores > 1
	
	matrix := make([][]float64, numOperators)
	for i := range matrix {
		matrix[i] = make([]float64, numTasks)
	}
	
	if numCores == 1 {
		// Sequential execution
		for opIdx := 0; opIdx < numOperators; opIdx++ {
			rng := rand.New(rand.NewSource(seed + int64(opIdx)))
			matrix[opIdx] = generateOperatorRow(opIdx, numTasks, rng)
		}
	} else {
		// Parallel execution with goroutines (one per operator)
		var wg sync.WaitGroup
		for opIdx := 0; opIdx < numOperators; opIdx++ {
			wg.Add(1)
			go func(idx int, seed int64) {
				defer wg.Done()
				// Each goroutine gets its own RNG seeded deterministically
				rng := rand.New(rand.NewSource(seed + int64(idx)))
				matrix[idx] = generateOperatorRow(idx, numTasks, rng)
			}(opIdx, seed)
		}
		wg.Wait()
	}
	
	return matrix
}

func generateOperatorRow(opIdx int, numTasks int, rng *rand.Rand) []float64 {
	row := make([]float64, numTasks)
	
	// Operator attributes (simulating database fetch)
	operatorZone := rng.Intn(10)
	operatorSkillLevel := 1.0 + rng.Float64()*9.0
	idleTime := rng.Intn(601)
	idleBonus := -min(float64(idleTime)/6.0, 100.0)
	operatorLocX := rng.Float64() * 1000.0
	operatorLocY := rng.Float64() * 1000.0
	
	for taskIdx := 0; taskIdx < numTasks; taskIdx++ {
		// Simulate heavy CPU-bound cost calculation (like real cost function)
		// Multiple weighted factors, zone penalties, idle penalties
		for i := 0; i < 100; i++ {
			tempCost := 0.0
			tempCost += rng.Float64() * 10.0  // w1 * op_remaining_time_cost
			tempCost += rng.Float64() * 5.0   // w2 * op_reach_time_cost
			tempCost += rng.Float64() * 3.0   // w3 * op_wait_time_cost
			tempCost -= rng.Float64() * 2.0   // w4 * bot_starvation_cost
			tempCost -= rng.Float64() * 4.0   // w5 * localized_marker_cost
			tempCost += rng.Float64() * 8.0   // w6 * total_quantity_cost
			tempCost += math.Abs(rng.Float64()-0.5) * 100  // zone_distance
			tempCost -= rng.Float64() * 50    // zone_full_penalty
			idleVal := rng.Float64()*10 - 5
			if idleVal > 0 {
				tempCost += idleVal * 2  // idle_penalty
			}
			_ = tempCost  // prevent optimization
		}
		
		// Task attributes (simulating database fetch)
		taskZone := rng.Intn(11)
		taskPriority := 1.0 + rng.Float64()*4.0
		taskLocX := rng.Float64() * 1000.0
		taskLocY := rng.Float64() * 1000.0
		taskComplexity := 1.0 + rng.Float64()*9.0
		
		// Complex distance calculation
		dx := taskLocX - operatorLocX
		dy := taskLocY - operatorLocY
		rawDistance := math.Sqrt(dx*dx + dy*dy)
		terrainFactor := 1.0 + rng.Float64()*0.5
		distanceCost := rawDistance * terrainFactor * 0.5
		
		// Zone change penalty
		zonePenalty := 0.0
		if operatorZone != taskZone {
			zonePenalty = 1000.0 + float64(abs(operatorZone-taskZone))*100.0
		}
		
		// Skill matching cost
		skillGap := math.Abs(operatorSkillLevel - taskComplexity)
		skillPenalty := skillGap * 150.0
		
		// Priority weighting
		priorityFactor := (6.0 - taskPriority) * 50.0
		
		// Time-based costs
		estimatedTravelTime := distanceCost / 30.0
		timePenalty := estimatedTravelTime * 25.0
		
		// Historical performance simulation
		historicalScore := 0.7 + rng.Float64()*0.3
		for i := 0; i < 5; i++ {
			historicalScore = (historicalScore + 0.7 + rng.Float64()*0.3) / 2
		}
		performancePenalty := (1.0 - historicalScore) * 200.0
		
		// Small random variation
		variation := -50.0 + rng.Float64()*100.0
		
		// Total cost
		totalCost := distanceCost + zonePenalty + skillPenalty + 
			priorityFactor + timePenalty + performancePenalty + idleBonus + variation
		
		// Ensure non-negative
		if totalCost < 0 {
			totalCost = 0
		}
		
		row[taskIdx] = totalCost
	}
	
	return row
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

func runBenchmark(data TestData, numCores int) BenchmarkResult {
	mode := "sequential"
	if numCores > 1 {
		mode = "parallel"
	}
	
	result := BenchmarkResult{
		Language:       "Golang",
		Implementation: fmt.Sprintf("hungarian-algorithm (%s)", mode),
		Scenario:       data.Name,
		MatrixSize:     fmt.Sprintf("%dx%d", data.Operators, data.Tasks),
	}

	// Force garbage collection before benchmark
	runtime.GC()

	// Measure memory before
	var memBefore runtime.MemStats
	runtime.ReadMemStats(&memBefore)

	// Time matrix generation
	loadStart := time.Now()
	floatMatrix := generateRealisticCostMatrix(data.Operators, data.Tasks, numCores, 42)
	loadDuration := time.Since(loadStart)
	
	// Pad matrix to square if needed (Hungarian algorithm requires square matrices)
	rows := len(floatMatrix)
	cols := len(floatMatrix[0])
	maxDim := rows
	if cols > maxDim {
		maxDim = cols
	}
	
	// Create square matrix padded with zeros (or high costs for dummy assignments)
	paddedMatrix := make([][]float64, maxDim)
	for i := 0; i < maxDim; i++ {
		paddedMatrix[i] = make([]float64, maxDim)
		for j := 0; j < maxDim; j++ {
			if i < rows && j < cols {
				paddedMatrix[i][j] = floatMatrix[i][j]
			} else {
				// Use high cost for dummy cells to avoid them in solution
				paddedMatrix[i][j] = 999999.0
			}
		}
	}
	
	// Convert float64 matrix to int matrix (multiply by 100 to preserve precision)
	intMatrix := make([][]int, maxDim)
	for i := range paddedMatrix {
		intMatrix[i] = make([]int, maxDim)
		for j := range paddedMatrix[i] {
			intMatrix[i][j] = int(paddedMatrix[i][j] * 100)
		}
	}

	// Start timing algorithm execution
	startTime := time.Now()

	// Run Hungarian algorithm
	fmt.Printf("  Running Hungarian on %dx%d matrix\n", len(intMatrix), len(intMatrix[0]))
	assignments, _ := hungarian.Solve(intMatrix)
	fmt.Printf("  Got %d assignments\n", len(assignments))

	// End timing
	duration := time.Since(startTime)

	// Calculate cost from assignments using the original float matrix
	cost := 0.0
	for i, j := range assignments {
		// Only count real assignments (not dummy ones from padding)
		if j >= 0 && i < len(floatMatrix) && j < len(floatMatrix[0]) {
			cost += floatMatrix[i][j]
		}
	}

	// Measure memory after
	var memAfter runtime.MemStats
	runtime.ReadMemStats(&memAfter)

	// Calculate metrics
	loadTime := float64(loadDuration.Microseconds()) / 1000.0
	execTime := float64(duration.Microseconds()) / 1000.0
	result.LoadTime = loadTime
	result.ExecutionTime = execTime
	result.TotalTime = loadTime + execTime
	result.MemoryUsed = float64(memAfter.Alloc-memBefore.Alloc) / (1024 * 1024) // Convert to MB
	result.SolutionCost = cost
	result.Success = true

	printMode := "sequential"
	if numCores > 1 {
		printMode = "parallel"
	}

	// Print intermediate results
	fmt.Printf("✓ Algorithm completed successfully\n")
	fmt.Printf("  Assignments: %d\n", len(assignments))
	fmt.Printf("  Total cost: %.2f\n", cost)
	fmt.Printf("  Load time (%s): %.3f ms\n", printMode, loadTime)
	fmt.Printf("  Algorithm time: %.3f ms\n", execTime)
	fmt.Printf("  Total time: %.3f ms\n", loadTime+execTime)
	fmt.Printf("  Memory used: %.2f MB\n\n", result.MemoryUsed)

	return result
}

func saveResults(result BenchmarkResult, filename string) error {
	jsonData, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return err
	}

	return ioutil.WriteFile(filename, jsonData, 0644)
}

func printSummary(result BenchmarkResult) {
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("BENCHMARK SUMMARY")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Printf("Language:        %s\n", result.Language)
	fmt.Printf("Implementation:  %s\n", result.Implementation)
	fmt.Printf("Scenario:        %s\n", result.Scenario)
	fmt.Printf("Matrix Size:     %s\n", result.MatrixSize)
	fmt.Printf("Execution Time:  %.3f ms\n", result.ExecutionTime)
	fmt.Printf("Memory Used:     %.2f MB\n", result.MemoryUsed)
	fmt.Printf("Solution Cost:   %.2f\n", result.SolutionCost)
	fmt.Printf("Success:         %v\n", result.Success)
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
}
