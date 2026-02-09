use serde::{Deserialize, Serialize};
use std::env;
use std::fs::File;
use std::io::{BufReader, Write};
use std::time::Instant;
use pathfinding::kuhn_munkres::{kuhn_munkres, Weights};
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;
use rayon::prelude::*;

#[derive(Debug, Deserialize)]
struct TestData {
    name: String,
    operators: usize,
    tasks: usize,
    matrix: Vec<Vec<f64>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BenchmarkResult {
    language: String,
    implementation: String,
    scenario: String,
    matrix_size: String,
    load_time_ms: f64,
    execution_time_ms: f64,
    total_time_ms: f64,
    memory_used_mb: u64,
    solution_cost: f64,
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error_msg: Option<String>,
}

fn load_test_data(filename: &str) -> Result<TestData, Box<dyn std::error::Error>> {
    let file = File::open(filename)?;
    let reader = BufReader::new(file);
    let data: TestData = serde_json::from_reader(reader)?;
    Ok(data)
}

fn generate_realistic_cost_matrix(num_operators: usize, num_tasks: usize, num_cores: usize, seed: u64) -> Vec<Vec<f64>> {
    // Generate realistic cost matrix simulating heavy OGA allocation cost computation
    // Uses rayon for parallel or sequential execution based on num_cores
    if num_cores == 1 {
        // Sequential execution
        (0..num_operators)
            .map(|op_idx| generate_operator_row(op_idx, num_tasks, seed))
            .collect()
    } else {
        // Parallel execution with rayon
        (0..num_operators)
            .into_par_iter()
            .map(|op_idx| generate_operator_row(op_idx, num_tasks, seed))
            .collect()
    }
}

fn generate_operator_row(op_idx: usize, num_tasks: usize, seed: u64) -> Vec<f64> {
    // Generate a single operator row (called in parallel)
    let mut rng = StdRng::seed_from_u64(seed + op_idx as u64);
    let mut row = Vec::with_capacity(num_tasks);
    
    // Operator attributes (simulating database fetch)
    let operator_zone = rng.gen_range(0..10);
    let operator_skill_level: f64 = rng.gen_range(1.0..10.0);
    let idle_time = rng.gen_range(0..=600);
    let idle_bonus = -((idle_time as f64 / 6.0).min(100.0));
    let operator_loc_x: f64 = rng.gen_range(0.0..1000.0);
    let operator_loc_y: f64 = rng.gen_range(0.0..1000.0);
    
    for _ in 0..num_tasks {
        // Simulate heavy CPU-bound cost calculation (like real cost function)
        // Multiple weighted factors, zone penalties, idle penalties
        let mut temp_cost = 0.0;
        for _ in 0..100 {
            temp_cost += rng.gen::<f64>() * 10.0;  // w1 * op_remaining_time_cost
            temp_cost += rng.gen::<f64>() * 5.0;   // w2 * op_reach_time_cost
            temp_cost += rng.gen::<f64>() * 3.0;   // w3 * op_wait_time_cost
            temp_cost -= rng.gen::<f64>() * 2.0;   // w4 * bot_starvation_cost
            temp_cost -= rng.gen::<f64>() * 4.0;   // w5 * localized_marker_cost
            temp_cost += rng.gen::<f64>() * 8.0;   // w6 * total_quantity_cost
            temp_cost += (rng.gen::<f64>() - 0.5).abs() * 100.0;  // zone_distance
            temp_cost -= rng.gen::<f64>() * 50.0;  // zone_full_penalty
            let idle_val = rng.gen::<f64>() * 10.0 - 5.0;
            if idle_val > 0.0 {
                temp_cost += idle_val * 2.0;  // idle_penalty
            }
        }
        let _ = temp_cost;  // Prevent optimization
        
        // Task attributes (simulating database fetch)
        let task_zone = rng.gen_range(0..11);
        let task_priority: f64 = rng.gen_range(1.0..5.0);
        let task_loc_x: f64 = rng.gen_range(0.0..1000.0);
        let task_loc_y: f64 = rng.gen_range(0.0..1000.0);
        let task_complexity: f64 = rng.gen_range(1.0..10.0);
        
        // Complex distance calculation
        let dx: f64 = task_loc_x - operator_loc_x;
        let dy: f64 = task_loc_y - operator_loc_y;
        let raw_distance = (dx * dx + dy * dy).sqrt();
        let terrain_factor = 1.0 + rng.gen_range(0.0..0.5);
        let distance_cost = raw_distance * terrain_factor * 0.5;
        
        // Zone change penalty
        let zone_penalty = if operator_zone != task_zone {
            1000.0 + ((operator_zone as i32 - task_zone as i32).abs() as f64 * 100.0)
        } else {
            0.0
        };
        
        // Skill matching cost
        let skill_gap: f64 = (operator_skill_level - task_complexity).abs();
        let skill_penalty = skill_gap * 150.0;
        
        // Priority weighting
        let priority_factor = (6.0 - task_priority) * 50.0;
        
        // Time-based costs
        let estimated_travel_time = distance_cost / 30.0;
        let time_penalty = estimated_travel_time * 25.0;
        
        // Historical performance simulation
        let mut historical_score = rng.gen_range(0.7..1.0);
        for _ in 0..5 {
            historical_score = (historical_score + rng.gen_range(0.7..1.0)) / 2.0;
        }
        let performance_penalty = (1.0 - historical_score) * 200.0;
        
        // Small random variation
        let variation = rng.gen_range(-50.0..=50.0);
        
        // Total cost
        let mut total_cost = distance_cost + zone_penalty + skill_penalty + 
            priority_factor + time_penalty + performance_penalty + idle_bonus + variation;
        
        // Ensure non-negative
        if total_cost < 0.0 {
            total_cost = 0.0;
        }
        
        row.push((total_cost * 100.0).round() / 100.0);
    }
    
    row
}

fn convert_to_weights(matrix: &[Vec<f64>]) -> Vec<Vec<i64>> {
    // Convert float matrix to integer weights for pathfinding library
    // Multiply by 100 to preserve 2 decimal places
    // Negate values here to avoid expensive copy in kuhn_munkres_min
    matrix
        .iter()
        .map(|row| {
            row.iter()
                .map(|&val| -((val * 100.0).round() as i64))
                .collect()
        })
        .collect()
}

fn run_benchmark(data: TestData, num_cores: usize) -> BenchmarkResult {
    let mode = if num_cores > 1 { "parallel" } else { "sequential" };
    let mut result = BenchmarkResult {
        language: "Rust".to_string(),
        implementation: format!("pathfinding::kuhn_munkres ({})", mode),
        scenario: data.name.clone(),
        matrix_size: format!("{}x{}", data.operators, data.tasks),
        load_time_ms: 0.0,
        execution_time_ms: 0.0,
        total_time_ms: 0.0,
        memory_used_mb: 0,
        solution_cost: 0.0,
        success: false,
        error_msg: None,
    };

    // Get memory usage before (rough estimate)
    let mem_before = get_memory_usage();
    
    // Time matrix generation
    let load_start = Instant::now();
    let matrix = generate_realistic_cost_matrix(data.operators, data.tasks, num_cores, 42);
    let weights = convert_to_weights(&matrix);
    
    // Create a Weights instance
    struct MatrixWeights(Vec<Vec<i64>>);
    
    impl Weights<i64> for MatrixWeights {
        fn rows(&self) -> usize {
            self.0.len()
        }
        fn columns(&self) -> usize {
            self.0.get(0).map_or(0, |row| row.len())
        }
        fn at(&self, row: usize, col: usize) -> i64 {
            self.0[row][col]
        }
        fn neg(&self) -> Self {
            // Return a new instance with negated weights
            let negated = self.0.iter()
                .map(|row| row.iter().map(|&val| -val).collect())
                .collect();
            MatrixWeights(negated)
        }
    }
    
    let matrix_weights = MatrixWeights(weights);
    let load_duration = load_start.elapsed();
    
    // Start timing algorithm execution
    let start = Instant::now();
    
    // Run Hungarian algorithm (matrix already negated, use max version)
    let (_negative_cost, assignments) = kuhn_munkres(&matrix_weights);
    
    // End timing
    let duration = start.elapsed();
    
    // Get memory usage after
    let mem_after = get_memory_usage();
    
    // Calculate solution cost from generated matrix (not scaled)
    let mut actual_cost = 0.0;
    for (row, &col) in assignments.iter().enumerate() {
        if row < matrix.len() && col < matrix[row].len() {
            actual_cost += matrix[row][col];
        }
    }
    
    let load_time = load_duration.as_secs_f64() * 1000.0;
    let exec_time = duration.as_secs_f64() * 1000.0;
    result.load_time_ms = load_time;
    result.execution_time_ms = exec_time;
    result.total_time_ms = load_time + exec_time;
    result.memory_used_mb = (mem_after.saturating_sub(mem_before)) / (1024 * 1024);
    result.solution_cost = actual_cost;
    result.success = true;
    
    println!("✓ Algorithm completed successfully");
    println!("  Assignments: {}", assignments.len());
    println!("  Total cost: {:.2}", actual_cost);
    let mode = if num_cores > 1 { "parallel" } else { "sequential" };
    println!("  Load time ({}): {:.3} ms", mode, load_time);
    println!("  Algorithm time: {:.3} ms", exec_time);
    println!("  Total time: {:.3} ms", load_time + exec_time);
    println!("  Memory used: {} MB\n", result.memory_used_mb);
    
    result
}

fn get_memory_usage() -> u64 {
    // Simple memory usage estimation
    // In production, you'd use a proper memory profiler
    #[cfg(target_os = "linux")]
    {
        if let Ok(status) = std::fs::read_to_string("/proc/self/status") {
            for line in status.lines() {
                if line.starts_with("VmRSS:") {
                    if let Some(kb) = line.split_whitespace().nth(1) {
                        if let Ok(kb_val) = kb.parse::<u64>() {
                            return kb_val * 1024; // Convert to bytes
                        }
                    }
                }
            }
        }
    }
    0 // Return 0 if we can't determine
}

fn save_results(result: &BenchmarkResult, filename: &str) -> Result<(), Box<dyn std::error::Error>> {
    let json = serde_json::to_string_pretty(result)?;
    let mut file = File::create(filename)?;
    file.write_all(json.as_bytes())?;
    Ok(())
}

fn print_summary(result: &BenchmarkResult) {
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("BENCHMARK SUMMARY");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Language:        {}", result.language);
    println!("Implementation:  {}", result.implementation);
    println!("Scenario:        {}", result.scenario);
    println!("Matrix Size:     {}", result.matrix_size);
    
    if result.success {
        println!("Execution Time:  {:.3} ms", result.execution_time_ms);
        println!("Memory Used:     {} MB", result.memory_used_mb);
        println!("Solution Cost:   {:.2}", result.solution_cost);
        println!("Success:         ✓");
    } else {
        println!("Success:         ✗");
        if let Some(ref err) = result.error_msg {
            println!("Error:           {}", err);
        }
    }
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 4 {
        eprintln!("Usage: hungarian-benchmark <scenario_name> <num_operators> <num_tasks> [num_cores]");
        std::process::exit(1);
    }
    
    let scenario = &args[1];
    let num_operators: usize = args[2].parse().expect("Invalid number of operators");
    let num_tasks: usize = args[3].parse().expect("Invalid number of tasks");
    let num_cores: usize = if args.len() > 4 {
        args[4].parse().expect("Invalid number of cores")
    } else {
        1
    };
    
    // Initialize rayon thread pool explicitly
    if num_cores > 1 {
        rayon::ThreadPoolBuilder::new()
            .num_threads(num_cores)
            .build_global()
            .unwrap();
    }
    
    let mode = if num_cores > 1 { "PARALLEL" } else { "SEQUENTIAL" };
    
    println!("Running Rust Hungarian Algorithm Benchmark ({})", mode);
    println!("Scenario: {}", scenario);
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Matrix: {}×{} | Cores: {}\n", num_operators, num_tasks, num_cores);
    
    // Create data structure
    let data = TestData {
        name: scenario.to_string(),
        operators: num_operators,
        tasks: num_tasks,
        matrix: vec![], // Not used anymore
    };
    
    // Run benchmark
    let result = run_benchmark(data, num_cores);
    
    // Append results to consolidated file
    let output_file = "/results/rust_results.json";
    
    // Read existing results if file exists
    let mut results: Vec<BenchmarkResult> = if std::path::Path::new(output_file).exists() {
        match std::fs::read_to_string(output_file) {
            Ok(content) => serde_json::from_str(&content).unwrap_or_else(|_| Vec::new()),
            Err(_) => Vec::new(),
        }
    } else {
        Vec::new()
    };
    
    // Append new result
    results.push(result.clone());
    
    // Write back all results
    let json = serde_json::to_string_pretty(&results).expect("Failed to serialize results");
    std::fs::write(output_file, json).expect("Failed to write results file");
    
    println!("✓ Results appended to {}", output_file);
    
    // Print summary
    print_summary(&result);
}
