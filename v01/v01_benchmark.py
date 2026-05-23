import psycopg2
import time
import json
import statistics
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CONFIG = {
    "variation_id": "V01",
    "policy_type": "inline",
    "table_size": "large",
    "has_query_index": True,
    "has_policy_index": True,
    
    "db_host": "localhost",
    "db_port": "5432",
    "db_name": "tpch",
    "db_user": "rls_tester",
    "db_pass": "rls_tester_password", 
    
    "test_clerk": "Clerk#000000001",
    "auth_key": 3682,        
    "unauth_key": 1,         
    "missing_key": -1        
}

ITERATION_RUNS = [100, 1000, 10000]

# ==============================================================================
# TIMING FUNCTION
# ==============================================================================
def measure_query(conn, query, params, warmups, iterations, test_clerk):
    times_us = []
    with conn.cursor() as cur:
        cur.execute("SET rls.test_clerk = %s;", (test_clerk,))
        for _ in range(warmups):
            cur.execute(query, params)
            cur.fetchall()
        for _ in range(iterations):
            start_time = time.perf_counter()
            cur.execute(query, params)
            cur.fetchall() 
            end_time = time.perf_counter()
            times_us.append((end_time - start_time) * 1_000_000)
    return times_us

# ==============================================================================
# QUERY PLAN EXTRACTOR
# ==============================================================================
def save_query_plans(conn, query, test_cases, test_clerk, filename):
    print(f"--- Extracting Query Plans to {filename} ---")
    with conn.cursor() as cur:
        cur.execute("SET rls.test_clerk = %s;", (test_clerk,))
        with open(filename, "w") as f:
            f.write(f"EXPLAIN ANALYZE Output - Variation {CONFIG['variation_id']}\n")
            f.write("="*80 + "\n\n")
            for access_type, key in test_cases.items():
                f.write(f"--- Test Case: {access_type} (Key: {key}) ---\n")
                explain_query = f"EXPLAIN ANALYZE {query}"
                cur.execute(explain_query, (key,))
                plan_lines = cur.fetchall()
                for line in plan_lines:
                    f.write(line[0] + "\n")
                f.write("\n")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
def main():
    print(f"--- Starting Benchmark for {CONFIG['variation_id']} ---")
    try:
        conn = psycopg2.connect(
            host=CONFIG["db_host"], port=CONFIG["db_port"],
            dbname=CONFIG["db_name"], user=CONFIG["db_user"], password=CONFIG["db_pass"]
        )
        conn.autocommit = True 
    except Exception as e:
        print(f"Database connection failed: {e}")
        return

    query = "SELECT * FROM orders WHERE o_orderkey = %s;"
    test_cases = {"Authorized": CONFIG["auth_key"], "Unauthorized": CONFIG["unauth_key"], "Missing": CONFIG["missing_key"]}

    # 1. Extract query plans
    plan_filename = f"plan_{CONFIG['variation_id']}.txt"
    save_query_plans(conn, query, test_cases, CONFIG["test_clerk"], plan_filename)

    all_runs_data = {}
    sns.set_theme(style="whitegrid") 
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(f"RLS Execution Time Density - Variation {CONFIG['variation_id']}", fontsize=16, fontweight='bold')
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] 

    # 2. Run benchmark loops
    for idx, iterations in enumerate(ITERATION_RUNS):
        warmups = int(iterations * 0.05)
        print(f"\n>> Running block: {iterations} iterations ({warmups} warmups) <<")
        
        run_results = {}
        plot_data = []
        labels = list(test_cases.keys())

        for access_type, key in test_cases.items():
            print(f"   Measuring '{access_type}' queries...")
            times = measure_query(conn, query, (key,), warmups, iterations, CONFIG["test_clerk"])
            plot_data.append(times)
            run_results[access_type] = {
                "mean_time_us": round(statistics.mean(times), 3),
                "median_time_us": round(statistics.median(times), 3),
                "min_time_us": round(min(times), 3),
                "max_time_us": round(max(times), 3),
                "std_dev_us": round(statistics.stdev(times), 3) if len(times) > 1 else 0.0,
                "raw_times_us": [round(t, 3) for t in times]
            }
            
        all_runs_data[str(iterations)] = {
            "warmup_iterations": warmups,
            "measure_iterations": iterations,
            "results": run_results
        }

        # Subplot Generation
        ax = axes[idx]
        for i, (label, color) in enumerate(zip(labels, colors)):
            sns.kdeplot(plot_data[i], ax=ax, label=label, color=color, fill=True, alpha=0.35, linewidth=2)
            
        all_times_flat = [t for sublist in plot_data for t in sublist]
        sorted_times = sorted(all_times_flat)
        p01 = sorted_times[int(len(sorted_times) * 0.01)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        ax.set_xlim(p01 * 0.9, p95 * 1.1)
            
        ax.set_title(f"N = {iterations}", fontsize=14)
        ax.set_xlabel("Execution Time (Microseconds)", fontsize=12)
        
        if idx == 0:
            ax.set_ylabel("Density", fontsize=12)
            ax.legend(loc='upper right', fontsize=11, frameon=True, shadow=True)
        else:
            ax.set_ylabel("") 
        
        ax.grid(True, linestyle='--', which='major', color='lightgrey', alpha=0.7)
        ax.set_axisbelow(True) 

    conn.close()

    # Save JSON Output
    final_output = {
        "variation_id": CONFIG["variation_id"],
        "metadata": {"policy_type": CONFIG["policy_type"], "table_size": CONFIG["table_size"],
                     "has_query_index": CONFIG["has_query_index"], "has_policy_index": CONFIG["has_policy_index"]},
        "runs": all_runs_data
    }
    json_string = re.sub(r'\[\s+([\d\.\,\s\-]+)\s+\]', lambda m: '[' + re.sub(r'\s+', ' ', m.group(1)).strip() + ']', json.dumps(final_output, indent=4))
    with open(f"results_{CONFIG['variation_id']}.json", "w") as f:
        f.write(json_string)

    # Save Plot Output
    info_text = (f"Query Index: {CONFIG['has_query_index']}\nPolicy Index: {CONFIG['has_policy_index']}")
    fig.text(0.98, 0.02, info_text, transform=fig.transFigure, fontsize=10, verticalalignment='bottom', horizontalalignment='right',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='gray', alpha=0.8))
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 
    plt.savefig(f"plot_{CONFIG['variation_id']}.png", dpi=300, bbox_inches='tight')
    print("\n--- Benchmark Complete ---")

if __name__ == "__main__":
    main()