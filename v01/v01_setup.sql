-- ==============================================================================
-- V01 SETUP: Large Table | Inline Policy | Query Indexed | Policy Indexed
-- ==============================================================================

-- 1. Create a dedicated least-privilege role for testing
DROP ROLE IF EXISTS rls_tester;
CREATE ROLE rls_tester LOGIN PASSWORD 'rls_tester_pass';
GRANT USAGE ON SCHEMA public TO rls_tester;
GRANT SELECT ON orders TO rls_tester;

-- 2. Create the Policy Index
-- The Query index (o_orderkey) already exists via the TPC-H Primary Key.
-- We explicitly create an index for the Policy column (o_clerk).
CREATE INDEX IF NOT EXISTS idx_v01_policy ON orders(o_clerk);

-- 3. Enable Row Level Security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 4. Create the Inline Policy
CREATE POLICY inline_policy_v01 
ON orders 
FOR SELECT 
TO rls_tester 
USING (o_clerk = current_setting('rls.test_clerk', true));