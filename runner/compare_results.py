#!/usr/bin/env python3
"""
Compare benchmark results across languages
"""
import json
import os
import glob
from tabulate import tabulate
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


def load_results(results_dir="/results"):
    """Load all benchmark results from consolidated files"""
    results = []
    
    # Load from consolidated files
    for language_file in ['python_results.json', 'golang_results.json', 'rust_results.json']:
        filepath = os.path.join(results_dir, language_file)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    # data is an array of results
                    if isinstance(data, list):
                        results.extend(data)
                    else:
                        results.append(data)
            except Exception as e:
                print(f"Warning: Could not load {language_file}: {e}")
    
    return results


def group_by_scenario(results):
    """Group results by scenario"""
    scenarios = {}
    for result in results:
        scenario = result.get('scenario', 'unknown')
        if scenario not in scenarios:
            scenarios[scenario] = []
        scenarios[scenario].append(result)
    return scenarios


def calculate_speedup(results, baseline_lang='Python'):
    """Calculate speedup relative to baseline"""
    baseline_algo_time = None
    baseline_load_time = None
    
    # Find baseline times
    for result in results:
        if result['language'] == baseline_lang and result.get('success'):
            baseline_algo_time = result.get('execution_time_ms')
            baseline_load_time = result.get('load_time_ms', 0)
            break
    
    if baseline_algo_time is None:
        return results
    
    # Calculate speedup for each result
    for result in results:
        if result.get('success'):
            exec_time = result.get('execution_time_ms', 0)
            load_time = result.get('load_time_ms', 0)
            if exec_time > 0:
                result['algo_speedup'] = baseline_algo_time / exec_time
            else:
                result['algo_speedup'] = 0
            if load_time > 0 and baseline_load_time > 0:
                result['load_speedup'] = baseline_load_time / load_time
            else:
                result['load_speedup'] = 0
        else:
            result['algo_speedup'] = 0
            result['load_speedup'] = 0
    
    return results


def format_speedup(speedup):
    """Format speedup with color"""
    if speedup == 0:
        return "N/A"
    elif speedup >= 5:
        return f"{Fore.GREEN}★ {speedup:.2f}x{Style.RESET_ALL}"
    elif speedup >= 2:
        return f"{Fore.CYAN}{speedup:.2f}x{Style.RESET_ALL}"
    elif speedup >= 1:
        return f"{speedup:.2f}x"
    else:
        return f"{Fore.RED}{speedup:.2f}x{Style.RESET_ALL}"


def print_scenario_comparison(scenario_name, results):
    """Print comparison table for a scenario with separate tables for sequential and parallel"""
    print(f"\n{'=' * 100}")
    print(f"  {scenario_name.upper()}")
    print(f"{'=' * 100}\n")
    
    # Separate sequential and parallel results
    sequential_results = [r for r in results if 'sequential' in r.get('implementation', '').lower()]
    parallel_results = [r for r in results if 'parallel' in r.get('implementation', '').lower()]
    
    # Print Sequential Results
    if sequential_results:
        print(f"\n{Fore.CYAN}📊 SEQUENTIAL (1 Core){Style.RESET_ALL}\n")
        sequential_results = calculate_speedup(sequential_results)
        sequential_results.sort(key=lambda x: x.get('execution_time_ms', float('inf')))
        
        table_data = []
        for result in sequential_results:
            if result.get('success'):
                memory_mb = result.get('memory_used_mb', 0)
                row = [
                    result['language'],
                    result.get('implementation', 'N/A')[:30],
                    result['matrix_size'],
                    f"{result.get('load_time_ms', 0):.3f}",
                    f"{result['execution_time_ms']:.3f}",
                    f"{result.get('total_time_ms', 0):.3f}",
                    f"{memory_mb:.2f}",
                    format_speedup(result.get('load_speedup', 0)),
                    format_speedup(result.get('algo_speedup', 0)),
                    f"{result.get('solution_cost', 0):.2f}"
                ]
                table_data.append(row)
        
        headers = ["Language", "Implementation", "Matrix", "Matrix Gen (ms)", "Algo (ms)", "Total (ms)", "Memory (MB)", "Matrix Gen Speedup", "Algo Speedup", "Cost"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        successful = [r for r in sequential_results if r.get('success')]
        if successful:
            winner = successful[0]
            print(f"\n{Fore.GREEN}🏆 Fastest (Sequential): {winner['language']}{Style.RESET_ALL}")
    
    # Print Parallel Results
    if parallel_results:
        print(f"\n{Fore.CYAN}📊 PARALLEL (8 Cores){Style.RESET_ALL}\n")
        parallel_results = calculate_speedup(parallel_results)
        parallel_results.sort(key=lambda x: x.get('execution_time_ms', float('inf')))
        
        table_data = []
        for result in parallel_results:
            if result.get('success'):
                memory_mb = result.get('memory_used_mb', 0)
                row = [
                    result['language'],
                    result.get('implementation', 'N/A')[:30],
                    result['matrix_size'],
                    f"{result.get('load_time_ms', 0):.3f}",
                    f"{result['execution_time_ms']:.3f}",
                    f"{result.get('total_time_ms', 0):.3f}",
                    f"{memory_mb:.2f}",
                    format_speedup(result.get('load_speedup', 0)),
                    format_speedup(result.get('algo_speedup', 0)),
                    f"{result.get('solution_cost', 0):.2f}"
                ]
                table_data.append(row)
        
        headers = ["Language", "Implementation", "Matrix", "Matrix Gen (ms)", "Algo (ms)", "Total (ms)", "Memory (MB)", "Matrix Gen Speedup", "Algo Speedup", "Cost"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        successful = [r for r in parallel_results if r.get('success')]
        if successful:
            winner = successful[0]
            print(f"\n{Fore.GREEN}🏆 Fastest (Parallel): {winner['language']}{Style.RESET_ALL}")


def generate_markdown_report(scenarios, output_file="/results/comparison_report.md"):
    """Generate markdown report"""
    with open(output_file, 'w') as f:
        f.write("# Hungarian Algorithm Benchmark Results\n\n")
        f.write(f"Generated: {os.popen('date').read().strip()}\n\n")
        f.write("**Timing Breakdown:**\n")
        f.write("- **Matrix Gen (ms)**: Time to generate cost matrix at runtime (nested loops, random numbers, arithmetic)\n")
        f.write("- **Algo (ms)**: Pure Hungarian algorithm execution time\n")
        f.write("- **Total (ms)**: Matrix Gen + Algo\n\n")
        f.write("*Note: No file I/O - matrices are created in-memory to benchmark pure language performance.*\n\n")
        
        for scenario_name, results in sorted(scenarios.items()):
            f.write(f"\n## {scenario_name.upper()}\n\n")
            
            # Separate sequential and parallel
            sequential_results = [r for r in results if 'sequential' in r.get('implementation', '').lower()]
            parallel_results = [r for r in results if 'parallel' in r.get('implementation', '').lower()]
            
            # Sequential table
            if sequential_results:
                f.write("### Sequential (1 Core)\n\n")
                sequential_results = calculate_speedup(sequential_results)
                sequential_results.sort(key=lambda x: x.get('execution_time_ms', float('inf')))
                
                f.write("| Language | Implementation | Matrix | Matrix Gen (ms) | Algo (ms) | Total (ms) | Memory (MB) | Matrix Gen Speedup | Algo Speedup | Cost |\n")
                f.write("|----------|----------------|--------|-----------------|-----------|------------|-------------|---------------------|--------------|------|\n")
                
                for result in sequential_results:
                    if result.get('success'):
                        memory_mb = result.get('memory_used_mb', 0)
                        f.write(f"| {result['language']} ")
                        f.write(f"| {result.get('implementation', 'N/A')} ")
                        f.write(f"| {result['matrix_size']} ")
                        f.write(f"| {result.get('load_time_ms', 0):.3f} ")
                        f.write(f"| {result['execution_time_ms']:.3f} ")
                        f.write(f"| {result.get('total_time_ms', 0):.3f} ")
                        f.write(f"| {memory_mb:.2f} ")
                        load_speedup = result.get('load_speedup', 0)
                        f.write(f"| {load_speedup:.2f}x " if load_speedup > 0 else "| N/A ")
                        algo_speedup = result.get('algo_speedup', 0)
                        f.write(f"| {algo_speedup:.2f}x " if algo_speedup > 0 else "| N/A ")
                        f.write(f"| {result.get('solution_cost', 0):.2f} |\n")
                
                successful = [r for r in sequential_results if r.get('success')]
                if successful:
                    winner = successful[0]
                    f.write(f"\n**Fastest (Sequential):** {winner['language']}\n\n")
            
            # Parallel table
            if parallel_results:
                f.write("### Parallel (8 Cores)\n\n")
                parallel_results = calculate_speedup(parallel_results)
                parallel_results.sort(key=lambda x: x.get('execution_time_ms', float('inf')))
                
                f.write("| Language | Implementation | Matrix | Matrix Gen (ms) | Algo (ms) | Total (ms) | Memory (MB) | Matrix Gen Speedup | Algo Speedup | Cost |\n")
                f.write("|----------|----------------|--------|-----------------|-----------|------------|-------------|---------------------|--------------|------|\n")
                
                for result in parallel_results:
                    if result.get('success'):
                        memory_mb = result.get('memory_used_mb', 0)
                        f.write(f"| {result['language']} ")
                        f.write(f"| {result.get('implementation', 'N/A')} ")
                        f.write(f"| {result['matrix_size']} ")
                        f.write(f"| {result.get('load_time_ms', 0):.3f} ")
                        f.write(f"| {result['execution_time_ms']:.3f} ")
                        f.write(f"| {result.get('total_time_ms', 0):.3f} ")
                        f.write(f"| {memory_mb:.2f} ")
                        load_speedup = result.get('load_speedup', 0)
                        f.write(f"| {load_speedup:.2f}x " if load_speedup > 0 else "| N/A ")
                        algo_speedup = result.get('algo_speedup', 0)
                        f.write(f"| {algo_speedup:.2f}x " if algo_speedup > 0 else "| N/A ")
                        f.write(f"| {result.get('solution_cost', 0):.2f} |\n")
                
                successful = [r for r in parallel_results if r.get('success')]
                if successful:
                    winner = successful[0]
                    f.write(f"\n**Fastest (Parallel):** {winner['language']}\n\n")
            if successful:
                winner = successful[0]
                f.write(f"\n**Fastest Algorithm:** {winner['language']}")
                if winner.get('algo_speedup', 0) > 1:
                    f.write(f" ({winner['algo_speedup']:.2f}x faster than Python)")
                f.write("\n")
    
    print(f"\n📄 Markdown report saved to: {output_file}")


def generate_html_report(scenarios, output_file="/results/comparison_report.html"):
    """Generate HTML report"""
    with open(output_file, 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hungarian Algorithm Benchmark Results</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            margin: 0 0 10px 0;
            font-size: 2em;
        }
        .timestamp {
            opacity: 0.9;
            font-size: 0.9em;
        }
        .info-box {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .info-box h3 {
            margin-top: 0;
            color: #667eea;
        }
        .scenario {
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .scenario h2 {
            margin-top: 0;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .speedup-high {
            color: #10b981;
            font-weight: bold;
        }
        .speedup-medium {
            color: #3b82f6;
            font-weight: bold;
        }
        .speedup-low {
            color: #6b7280;
        }
        .winner {
            background: #dcfce7;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
            border-left: 4px solid #10b981;
        }
        .winner strong {
            color: #059669;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 Hungarian Algorithm Benchmark Results</h1>
""")
        f.write(f"        <div class='timestamp'>Generated: {os.popen('date').read().strip()}</div>\n")
        f.write("""    </div>
    
    <div class="info-box">
        <h3>📊 Timing Breakdown</h3>
        <ul>
            <li><strong>Matrix Gen (ms)</strong>: Time to generate cost matrix at runtime (nested loops, random numbers, arithmetic)</li>
            <li><strong>Algo (ms)</strong>: Pure Hungarian algorithm execution time</li>
            <li><strong>Total (ms)</strong>: Matrix Gen + Algo</li>
        </ul>
        <p><em>Note: No file I/O - matrices are created in-memory to benchmark pure language performance.</em></p>
    </div>
""")
        
        for scenario_name, results in sorted(scenarios.items()):
            # Separate sequential and parallel
            sequential_results = [r for r in results if 'sequential' in r.get('implementation', '').lower()]
            parallel_results = [r for r in results if 'parallel' in r.get('implementation', '').lower()]
            
            f.write(f"\n    <div class='scenario'>\n")
            f.write(f"        <h2>{scenario_name.upper()}</h2>\n")
            
            # Sequential table
            if sequential_results:
                sequential_results = calculate_speedup(sequential_results)
                sequential_results.sort(key=lambda x: x.get('execution_time_ms', float('inf')))
                
                f.write("        <h3>Sequential (1 Core)</h3>\n")
                f.write("        <table>\n")
                f.write("            <thead>\n")
                f.write("                <tr>\n")
                f.write("                    <th>Language</th>\n")
                f.write("                    <th>Implementation</th>\n")
                f.write("                    <th>Matrix</th>\n")
                f.write("                    <th>Matrix Gen (ms)</th>\n")
                f.write("                    <th>Algo (ms)</th>\n")
                f.write("                    <th>Total (ms)</th>\n")
                f.write("                    <th>Memory (MB)</th>\n")
                f.write("                    <th>Matrix Gen Speedup</th>\n")
                f.write("                    <th>Algo Speedup</th>\n")
                f.write("                    <th>Cost</th>\n")
                f.write("                </tr>\n")
                f.write("            </thead>\n")
                f.write("            <tbody>\n")
                
                for result in sequential_results:
                    if result.get('success'):
                        memory_mb = result.get('memory_used_mb', 0)
                        f.write("                <tr>\n")
                        f.write(f"                    <td><strong>{result['language']}</strong></td>\n")
                        f.write(f"                    <td>{result.get('implementation', 'N/A')}</td>\n")
                        f.write(f"                    <td>{result['matrix_size']}</td>\n")
                        f.write(f"                    <td>{result.get('load_time_ms', 0):.3f}</td>\n")
                        f.write(f"                    <td>{result['execution_time_ms']:.3f}</td>\n")
                        f.write(f"                    <td>{result.get('total_time_ms', 0):.3f}</td>\n")
                        f.write(f"                    <td>{memory_mb:.2f}</td>\n")
                        
                        load_speedup = result.get('load_speedup', 0)
                        if load_speedup >= 5:
                            f.write(f"                    <td class='speedup-high'>{load_speedup:.2f}x</td>\n")
                        elif load_speedup >= 2:
                            f.write(f"                    <td class='speedup-medium'>{load_speedup:.2f}x</td>\n")
                        elif load_speedup > 0:
                            f.write(f"                    <td class='speedup-low'>{load_speedup:.2f}x</td>\n")
                        else:
                            f.write("                    <td>N/A</td>\n")
                        
                        algo_speedup = result.get('algo_speedup', 0)
                        if algo_speedup >= 5:
                            f.write(f"                    <td class='speedup-high'>{algo_speedup:.2f}x</td>\n")
                        elif algo_speedup >= 2:
                            f.write(f"                    <td class='speedup-medium'>{algo_speedup:.2f}x</td>\n")
                        elif algo_speedup > 0:
                            f.write(f"                    <td class='speedup-low'>{algo_speedup:.2f}x</td>\n")
                        else:
                            f.write("                    <td>N/A</td>\n")
                        
                        f.write(f"                    <td>{result.get('solution_cost', 0):.2f}</td>\n")
                        f.write("                </tr>\n")
                
                f.write("            </tbody>\n")
                f.write("        </table>\n")
                
                successful = [r for r in sequential_results if r.get('success')]
                if successful:
                    winner = successful[0]
                    f.write("        <div class='winner'>\n")
                    f.write(f"            <strong>🏆 Fastest (Sequential):</strong> {winner['language']}")
                    if winner.get('algo_speedup', 0) > 1:
                        f.write(f" ({winner['algo_speedup']:.2f}x faster than Python)")
                    f.write("\n        </div>\n")
            
            # Parallel table
            if parallel_results:
                parallel_results = calculate_speedup(parallel_results)
                parallel_results.sort(key=lambda x: x.get('execution_time_ms', float('inf')))
                
                f.write("        <h3>Parallel (8 Cores)</h3>\n")
                f.write("        <table>\n")
                f.write("            <thead>\n")
                f.write("                <tr>\n")
                f.write("                    <th>Language</th>\n")
                f.write("                    <th>Implementation</th>\n")
                f.write("                    <th>Matrix</th>\n")
                f.write("                    <th>Matrix Gen (ms)</th>\n")
                f.write("                    <th>Algo (ms)</th>\n")
                f.write("                    <th>Total (ms)</th>\n")
                f.write("                    <th>Memory (MB)</th>\n")
                f.write("                    <th>Matrix Gen Speedup</th>\n")
                f.write("                    <th>Algo Speedup</th>\n")
                f.write("                    <th>Cost</th>\n")
                f.write("                </tr>\n")
                f.write("            </thead>\n")
                f.write("            <tbody>\n")
                
                for result in parallel_results:
                    if result.get('success'):
                        memory_mb = result.get('memory_used_mb', 0)
                        f.write("                <tr>\n")
                        f.write(f"                    <td><strong>{result['language']}</strong></td>\n")
                        f.write(f"                    <td>{result.get('implementation', 'N/A')}</td>\n")
                        f.write(f"                    <td>{result['matrix_size']}</td>\n")
                        f.write(f"                    <td>{result.get('load_time_ms', 0):.3f}</td>\n")
                        f.write(f"                    <td>{result['execution_time_ms']:.3f}</td>\n")
                        f.write(f"                    <td>{result.get('total_time_ms', 0):.3f}</td>\n")
                        f.write(f"                    <td>{memory_mb:.2f}</td>\n")
                        
                        load_speedup = result.get('load_speedup', 0)
                        if load_speedup >= 5:
                            f.write(f"                    <td class='speedup-high'>{load_speedup:.2f}x</td>\n")
                        elif load_speedup >= 2:
                            f.write(f"                    <td class='speedup-medium'>{load_speedup:.2f}x</td>\n")
                        elif load_speedup > 0:
                            f.write(f"                    <td class='speedup-low'>{load_speedup:.2f}x</td>\n")
                        else:
                            f.write("                    <td>N/A</td>\n")
                        
                        algo_speedup = result.get('algo_speedup', 0)
                        if algo_speedup >= 5:
                            f.write(f"                    <td class='speedup-high'>{algo_speedup:.2f}x</td>\n")
                        elif algo_speedup >= 2:
                            f.write(f"                    <td class='speedup-medium'>{algo_speedup:.2f}x</td>\n")
                        elif algo_speedup > 0:
                            f.write(f"                    <td class='speedup-low'>{algo_speedup:.2f}x</td>\n")
                        else:
                            f.write("                    <td>N/A</td>\n")
                        
                        f.write(f"                    <td>{result.get('solution_cost', 0):.2f}</td>\n")
                        f.write("                </tr>\n")
                
                f.write("            </tbody>\n")
                f.write("        </table>\n")
                
                successful = [r for r in parallel_results if r.get('success')]
                if successful:
                    winner = successful[0]
                    f.write("        <div class='winner'>\n")
                    f.write(f"            <strong>🏆 Fastest (Parallel):</strong> {winner['language']}")
                    if winner.get('algo_speedup', 0) > 1:
                        f.write(f" ({winner['algo_speedup']:.2f}x faster than Python)")
                    f.write("\n        </div>\n")
            
            f.write("    </div>\n")
        
        f.write("""</body>
</html>
""")
    
    print(f"📄 HTML report saved to: {output_file}")


def generate_confluence_report(scenarios, output_file="/results/comparison_report_confluence.txt"):
    """Generate Confluence Wiki Markup report"""
    with open(output_file, 'w') as f:
        f.write("h1. Hungarian Algorithm Benchmark Results\n\n")
        f.write(f"*Generated:* {os.popen('date').read().strip()}\n\n")
        
        f.write("{panel:title=Timing Breakdown|borderStyle=solid|borderColor=#ccc|titleBGColor=#667eea|bgColor=#f5f5f5}\n")
        f.write("* *Matrix Gen (ms)*: Time to generate cost matrix at runtime (nested loops, random numbers, arithmetic)\n")
        f.write("* *Algo (ms)*: Pure Hungarian algorithm execution time\n")
        f.write("* *Total (ms)*: Matrix Gen + Algo\n\n")
        f.write("_Note: No file I/O - matrices are created in-memory to benchmark pure language performance._\n")
        f.write("{panel}\n\n")
        
        for scenario_name, results in sorted(scenarios.items()):
            # Separate sequential and parallel
            sequential_results = [r for r in results if 'sequential' in r.get('implementation', '').lower()]
            parallel_results = [r for r in results if 'parallel' in r.get('implementation', '').lower()]
            
            f.write(f"h2. {scenario_name.upper()}\n\n")
            
            # Sequential table
            if sequential_results:
                sequential_results = calculate_speedup(sequential_results)
                sequential_results.sort(key=lambda x: x.get('execution_time_ms', float('inf')))
                
                f.write("h3. Sequential (1 Core)\n\n")
                f.write("|| Language || Implementation || Matrix || Matrix Gen (ms) || Algo (ms) || Total (ms) || Memory (MB) || Matrix Gen Speedup || Algo Speedup || Cost ||\n")
                
                for result in sequential_results:
                    if result.get('success'):
                        memory_mb = result.get('memory_used_mb', 0)
                        f.write(f"| *{result['language']}* ")
                        f.write(f"| {result.get('implementation', 'N/A')} ")
                        f.write(f"| {result['matrix_size']} ")
                        f.write(f"| {result.get('load_time_ms', 0):.3f} ")
                        f.write(f"| {result['execution_time_ms']:.3f} ")
                        f.write(f"| {result.get('total_time_ms', 0):.3f} ")
                        f.write(f"| {memory_mb:.2f} ")
                        
                        load_speedup = result.get('load_speedup', 0)
                        if load_speedup >= 2:
                            f.write(f"| {{color:#10b981}}*{load_speedup:.2f}x*{{color}} ")
                        elif load_speedup > 0:
                            f.write(f"| {load_speedup:.2f}x ")
                        else:
                            f.write("| N/A ")
                        
                        algo_speedup = result.get('algo_speedup', 0)
                        if algo_speedup >= 2:
                            f.write(f"| {{color:#10b981}}*{algo_speedup:.2f}x*{{color}} ")
                        elif algo_speedup > 0:
                            f.write(f"| {algo_speedup:.2f}x ")
                        else:
                            f.write("| N/A ")
                        
                        f.write(f"| {result.get('solution_cost', 0):.2f} |\n")
                
                successful = [r for r in sequential_results if r.get('success')]
                if successful:
                    winner = successful[0]
                    f.write("\n{info:title=Winner (Sequential)}\n")
                    f.write(f"*Fastest:* {winner['language']}")
                    if winner.get('algo_speedup', 0) > 1:
                        f.write(f" ({winner['algo_speedup']:.2f}x faster than Python)")
                    f.write("\n{info}\n\n")
            
            # Parallel table
            if parallel_results:
                parallel_results = calculate_speedup(parallel_results)
                parallel_results.sort(key=lambda x: x.get('execution_time_ms', float('inf')))
                
                f.write("h3. Parallel (8 Cores)\n\n")
                f.write("|| Language || Implementation || Matrix || Matrix Gen (ms) || Algo (ms) || Total (ms) || Memory (MB) || Matrix Gen Speedup || Algo Speedup || Cost ||\n")
                
                for result in parallel_results:
                    if result.get('success'):
                        memory_mb = result.get('memory_used_mb', 0)
                        f.write(f"| *{result['language']}* ")
                        f.write(f"| {result.get('implementation', 'N/A')} ")
                        f.write(f"| {result['matrix_size']} ")
                        f.write(f"| {result.get('load_time_ms', 0):.3f} ")
                        f.write(f"| {result['execution_time_ms']:.3f} ")
                        f.write(f"| {result.get('total_time_ms', 0):.3f} ")
                        f.write(f"| {memory_mb:.2f} ")
                        
                        load_speedup = result.get('load_speedup', 0)
                        if load_speedup >= 2:
                            f.write(f"| {{color:#10b981}}*{load_speedup:.2f}x*{{color}} ")
                        elif load_speedup > 0:
                            f.write(f"| {load_speedup:.2f}x ")
                        else:
                            f.write("| N/A ")
                        
                        algo_speedup = result.get('algo_speedup', 0)
                        if algo_speedup >= 2:
                            f.write(f"| {{color:#10b981}}*{algo_speedup:.2f}x*{{color}} ")
                        elif algo_speedup > 0:
                            f.write(f"| {algo_speedup:.2f}x ")
                        else:
                            f.write("| N/A ")
                        
                        f.write(f"| {result.get('solution_cost', 0):.2f} |\n")
                
                successful = [r for r in parallel_results if r.get('success')]
                if successful:
                    winner = successful[0]
                    f.write("\n{info:title=Winner (Parallel)}\n")
                    f.write(f"*Fastest:* {winner['language']}")
                    if winner.get('algo_speedup', 0) > 1:
                        f.write(f" ({winner['algo_speedup']:.2f}x faster than Python)")
                    f.write("\n{info}\n\n")
    
    print(f"📄 Confluence report saved to: {output_file}")


def main():
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"  HUNGARIAN ALGORITHM BENCHMARK - COMPARISON RESULTS")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")
    
    # Load results
    results = load_results()
    
    if not results:
        print(f"{Fore.RED}No results found in /results/{Style.RESET_ALL}")
        return
    
    print(f"Loaded {len(results)} benchmark results\n")
    
    # Group by scenario
    scenarios = group_by_scenario(results)
    
    # Print comparisons for each scenario
    for scenario_name, scenario_results in sorted(scenarios.items()):
        print_scenario_comparison(scenario_name, scenario_results)
    
    # Generate all report formats
    generate_markdown_report(scenarios)
    generate_html_report(scenarios)
    generate_confluence_report(scenarios)
    
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")


if __name__ == '__main__':
    main()
