#!/usr/bin/env python3
"""
Python Hungarian Algorithm Benchmark using scipy with multiprocessing
"""
import json
import os
import sys
import time
import traceback
import random
import psutil
import numpy as np
from scipy.optimize import linear_sum_assignment
from multiprocessing import Pool, cpu_count


def generate_operator_row(args):
    """Generate a single operator row (called in parallel)"""
    op_idx, num_tasks, seed = args
    random.seed(seed)
    operator_row = []
    
    # Operator attributes (simulating database fetch)
    operator_zone = random.randint(0, 9)
    operator_skill_level = random.uniform(1.0, 10.0)
    idle_time = random.randint(0, 600)
    idle_bonus = -min(idle_time / 6.0, 100.0)
    operator_location = (random.uniform(0, 1000), random.uniform(0, 1000))
    
    for task_idx in range(num_tasks):
        # Simulate heavy CPU-bound cost calculation (like your real cost function)
        # Multiple weighted factors, zone penalties, idle penalties
        for _ in range(100):  # Simulate complex computation iterations
            temp_cost = 0.0
            temp_cost += random.random() * 10.0  # w1 * op_remaining_time_cost
            temp_cost += random.random() * 5.0   # w2 * op_reach_time_cost  
            temp_cost += random.random() * 3.0   # w3 * op_wait_time_cost
            temp_cost -= random.random() * 2.0   # w4 * bot_starvation_cost
            temp_cost -= random.random() * 4.0   # w5 * localized_marker_cost
            temp_cost += random.random() * 8.0   # w6 * total_quantity_cost
            temp_cost += abs(random.random() - 0.5) * 100  # zone_distance
            temp_cost -= random.random() * 50    # zone_full_penalty
            temp_cost += max(random.random() * 10 - 5, 0) * 2  # idle_penalty
        
        task_zone = random.randint(0, 10)
        task_priority = random.uniform(1.0, 5.0)
        task_location = (random.uniform(0, 1000), random.uniform(0, 1000))
        task_complexity = random.uniform(1.0, 10.0)
        
        # Complex distance calculation (Euclidean with terrain factors)
        dx = task_location[0] - operator_location[0]
        dy = task_location[1] - operator_location[1]
        raw_distance = (dx**2 + dy**2)**0.5
        terrain_factor = 1.0 + random.uniform(0, 0.5)
        distance_cost = raw_distance * terrain_factor * 0.5
        
        # Zone change penalty (heavy computation)
        zone_penalty = 0.0
        if operator_zone != task_zone:
            zone_penalty = 1000.0 + (abs(operator_zone - task_zone) * 100)
        
        # Skill matching cost
        skill_gap = abs(operator_skill_level - task_complexity)
        skill_penalty = skill_gap * 150.0
        
        # Priority weighting
        priority_factor = (6.0 - task_priority) * 50.0
        
        # Time-based costs
        estimated_travel_time = distance_cost / 30.0  # 30 units/hour
        time_penalty = estimated_travel_time * 25.0
        
        # Historical performance simulation (complex calculation)
        historical_score = random.uniform(0.7, 1.0)
        for _ in range(5):  # Simulate averaging multiple records
            historical_score = (historical_score + random.uniform(0.7, 1.0)) / 2
        performance_penalty = (1.0 - historical_score) * 200.0
        
        # Small random variation
        variation = random.uniform(-50.0, 50.0)
        
        # Total cost with all factors
        total_cost = (
            distance_cost + 
            zone_penalty + 
            skill_penalty + 
            priority_factor + 
            time_penalty + 
            performance_penalty +
            idle_bonus + 
            variation
        )
        
        # Ensure non-negative
        total_cost = max(0, total_cost)
        
        operator_row.append(total_cost)
    
    return operator_row


def generate_realistic_cost_matrix(num_operators, num_tasks, num_cores=1, seed=42):
    """Generate realistic cost matrix using multiprocessing for parallel execution"""
    # Create arguments for each operator (with unique seed per operator)
    args = [(i, num_tasks, seed + i) for i in range(num_operators)]
    
    if num_cores == 1:
        # Sequential execution
        cost_matrix = [generate_operator_row(arg) for arg in args]
    else:
        # Parallel execution
        with Pool(processes=num_cores) as pool:
            cost_matrix = pool.map(generate_operator_row, args)
    
    return cost_matrix


def load_test_data(filename):
    """Load test data from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)


def run_benchmark(data):
    """Run Hungarian algorithm benchmark"""
    num_cores = data.get('num_cores', 1)
    mode = "parallel" if num_cores > 1 else "sequential"
    result = {
        'language': 'Python',
        'implementation': f'scipy.optimize.linear_sum_assignment ({mode})',
        'scenario': data['name'],
        'matrix_size': f"{data['operators']}x{data['tasks']}",
        'cores': num_cores,
        'success': False
    }

    try:
        # Measure memory before
        process = psutil.Process()
        mem_before = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Time matrix generation
        load_start = time.perf_counter()
        num_cores = data.get('num_cores', 1)
        matrix_data = generate_realistic_cost_matrix(data['operators'], data['tasks'], num_cores=num_cores)
        cost_matrix = np.array(matrix_data, dtype=np.float64)
        load_end = time.perf_counter()
        load_time = (load_end - load_start) * 1000  # Convert to milliseconds
        
        mode = "parallel" if num_cores > 1 else "sequential"
        print(f"Matrix shape: {cost_matrix.shape}")
        print(f"Matrix dtype: {cost_matrix.dtype}")
        print(f"Load time ({mode}): {load_time:.3f} ms")
        
        # Start timing algorithm execution
        start_time = time.perf_counter()
        
        # Run Hungarian algorithm
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        # End timing
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Measure memory after
        mem_after = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Calculate solution cost
        solution_cost = cost_matrix[row_indices, col_indices].sum()
        
        # Update result
        result['load_time_ms'] = round(load_time, 3)
        result['execution_time_ms'] = round(execution_time, 3)
        result['total_time_ms'] = round(load_time + execution_time, 3)
        result['memory_used_mb'] = round(mem_after - mem_before, 2)
        result['solution_cost'] = round(float(solution_cost), 2)
        result['assignments'] = len(row_indices)
        result['success'] = True
        
        print(f"\n✓ Algorithm completed successfully")
        print(f"  Assignments: {len(row_indices)}")
        print(f"  Total cost: {solution_cost:.2f}")
        print(f"  Load time: {load_time:.3f} ms")
        print(f"  Algorithm time: {execution_time:.3f} ms")
        print(f"  Total time: {load_time + execution_time:.3f} ms")
        print(f"  Memory used: {mem_after - mem_before:.2f} MB\n")
        
    except Exception as e:
        result['success'] = False
        result['error_msg'] = str(e)
        result['traceback'] = traceback.format_exc()
        print(f"\n✗ Error: {e}\n")
    
    return result


def save_results(result, filename):
    """Save results to JSON file"""
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)


def print_summary(result):
    """Print benchmark summary"""
    print("━" * 60)
    print("BENCHMARK SUMMARY")
    print("━" * 60)
    print(f"Language:        {result['language']}")
    print(f"Implementation:  {result['implementation']}")
    print(f"Scenario:        {result['scenario']}")
    print(f"Matrix Size:     {result['matrix_size']}")
    if result['success']:
        print(f"Execution Time:  {result['execution_time_ms']:.3f} ms")
        print(f"Memory Used:     {result['memory_used_mb']:.2f} MB")
        print(f"Solution Cost:   {result['solution_cost']:.2f}")
        print(f"Success:         ✓")
    else:
        print(f"Success:         ✗")
        print(f"Error:           {result.get('error_msg', 'Unknown error')}")
    print("━" * 60)


def main():
    if len(sys.argv) < 4:
        print("Usage: python main.py <scenario_name> <num_operators> <num_tasks> [num_cores]")
        sys.exit(1)
    
    scenario = sys.argv[1]
    num_operators = int(sys.argv[2])
    num_tasks = int(sys.argv[3])
    num_cores = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    
    mode = "PARALLEL" if num_cores > 1 else "SEQUENTIAL"
    print(f"Running Python Hungarian Algorithm Benchmark ({mode})")
    print(f"Scenario: {scenario}")
    print("━" * 60)
    print(f"Matrix: {num_operators}×{num_tasks} | Cores: {num_cores}\n")
    
    # Create data structure
    data = {
        'name': scenario,
        'operators': num_operators,
        'tasks': num_tasks,
        'num_cores': num_cores
    }
    
    # Run benchmark
    result = run_benchmark(data)
    
    # Append results to consolidated file
    output_file = "/results/python_results.json"
    try:
        # Read existing results if file exists
        results = []
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                results = json.load(f)
        
        # Append new result
        results.append(result)
        
        # Write back all results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Results appended to {output_file}")
    except Exception as e:
        print(f"Error saving results: {e}")
        sys.exit(1)
    
    # Print summary
    print_summary(result)


if __name__ == '__main__':
    main()
