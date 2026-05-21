#!/usr/bin/env python3
import time
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURATION ---
# Connection for setup/teardown (Needs Superuser or Owner privileges)
ADMIN_DB_CONFIG = {
    "dbname": "tpch",  
    "user": "root",       # Change to your admin user
    "password": "root", # Change to your admin password
    "host": "localhost"
}

# Connection for the benchmark (The restricted user)
ATTACKER_DB_CONFIG = {
    "dbname": "tpch",  
    "user": "rls_user",
    "password": "attack_password",
    "host": "localhost"
}

# Key Configuration
NON_EXISTENT_KEY = -1   # Q_k: Bypasses RLS completely
UNAUTHORIZED_KEY = 34   # Q_u: Exists, but user lacks permission (e.g., MACHINERY)
AUTHORIZED_KEY = 1     # Q_a: Exists, AND user has permission (e.g., AUTOMOBILE)

# --- SQL SCRIPTS ---
SETUP_SQL = """
-- 1. Forcefully clean up any remnants of rls_user from previous tests
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'rls_user') THEN
        DROP OWNED BY rls_user CASCADE;
        DROP ROLE rls_user;
    END IF;
END $$;

-- 2. Create the metadata table
DROP TABLE IF EXISTS rls_user_clearance CASCADE;
CREATE TABLE rls_user_clearance (
    username TEXT PRIMARY KEY,
    allowed_segment CHAR(10) NOT NULL
);

INSERT INTO rls_user_clearance (username, allowed_segment) 
VALUES ('rls_user', 'AUTOMOBILE');

-- 3. Provision the fresh role
CREATE ROLE rls_user WITH LOGIN PASSWORD 'attack_password';

GRANT SELECT ON orders TO rls_user;
GRANT SELECT ON customer TO rls_user;
GRANT SELECT ON rls_user_clearance TO rls_user;

-- 4. Enable RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS order_segment_policy ON orders;
CREATE POLICY order_segment_policy ON orders
FOR SELECT TO rls_user
USING (
    EXISTS (
        SELECT 1 FROM customer c
        JOIN rls_user_clearance p ON p.username = CURRENT_USER
        WHERE c.c_custkey = orders.o_custkey 
          AND c.c_mktsegment = p.allowed_segment
    )
);
"""

TEARDOWN_SQL = """
DROP POLICY IF EXISTS order_segment_policy ON orders;
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
DROP TABLE IF EXISTS rls_user_clearance CASCADE;

-- Forcefully clean up the user and all granted privileges
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'rls_user') THEN
        DROP OWNED BY rls_user CASCADE;
        DROP ROLE rls_user;
    END IF;
END $$;
"""

def execute_admin_sql(sql_script, step_name):
    """Executes structural SQL using the admin connection."""
    print(f"[*] Running {step_name}...")
    try:
        conn = psycopg2.connect(**ADMIN_DB_CONFIG)
        conn.autocommit = True # Required for CREATE/DROP ROLE commands
        cur = conn.cursor()
        cur.execute(sql_script)
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[!] {step_name} failed: {e}")
        exit(1)

def measure_queries(cur, query, key, iterations=5000, warmup=50):
    for _ in range(warmup):
        cur.execute(query, (key,))
        cur.fetchall()
        
    timings = []
    for _ in range(iterations):
        start = time.perf_counter()
        cur.execute(query, (key,))
        cur.fetchall()
        timings.append((time.perf_counter() - start) * 1e6)
        
    return timings

def main():
    # 1. Automated Setup
    execute_admin_sql(SETUP_SQL, "Database Setup")

    # 2. Connect as Restricted Attacker
    print("[*] Connecting as restricted user and normalizing optimizer...")
    try:
        conn = psycopg2.connect(**ATTACKER_DB_CONFIG)
        cur = conn.cursor()
    except Exception as e:
        print(f"[!] Attacker connection failed: {e}")
        execute_admin_sql(TEARDOWN_SQL, "Emergency Teardown")
        return

    cur.execute("SET jit = off;")
    cur.execute("SET max_parallel_workers_per_gather = 0;")
    cur.execute("SET plan_cache_mode = force_generic_plan;")

    query = "SELECT o_orderkey FROM orders WHERE o_orderkey = %s;"

    # 3. Benchmark All 3 States
    print("[*] Running benchmark (this may take a moment)...")
    qk_timings = measure_queries(cur, query, key=NON_EXISTENT_KEY) # Q_k
    qu_timings = measure_queries(cur, query, key=UNAUTHORIZED_KEY) # Q_u
    qa_timings = measure_queries(cur, query, key=AUTHORIZED_KEY)   # Q_a

    cur.close()
    conn.close()

    # 4. Automated Teardown
    execute_admin_sql(TEARDOWN_SQL, "Database Teardown")

    # 5. Visualization
    print("[*] Generating visualization...")
    plt.figure(figsize=(9, 5))
    
    sns.kdeplot(qk_timings, label="Dummy/Missing (Q_k)", fill=True, color="seagreen")
    sns.kdeplot(qu_timings, label="Unauthorized (Q_u)", fill=True, color="crimson")
    sns.kdeplot(qa_timings, label="Authorized (Q_a)", fill=True, color="royalblue")

    plt.xlim(120, 180) # Adjust based on your machine's baseline speed
    
    plt.title("RLS Timing Side-Channel (All 3 States)")
    plt.xlabel("Execution Time (μs)")
    plt.ylabel("Density")
    plt.legend()
    
    plt.tight_layout()
    plt.savefig("rls_plot_clean_3_states.pdf")
    print("[+] Saved plot to 'rls_plot_clean_3_states.pdf'")

if __name__ == "__main__":
    main()