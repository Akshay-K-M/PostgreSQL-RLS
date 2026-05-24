-- ==============================================================================
-- V03 SETUP: Large Table | Inline Policy | Query UNINDEXED | Policy INDEXED
-- ==============================================================================

-- 1. Create a dedicated least-privilege role for testing
DROP ROLE IF EXISTS rls_tester;
CREATE ROLE rls_tester LOGIN PASSWORD 'rls_tester_password';
GRANT USAGE ON SCHEMA public TO rls_tester;
GRANT SELECT ON orders TO rls_tester;

-- 2. Create the Policy Index
-- We explicitly create an index for the Policy column (o_clerk).
CREATE INDEX IF NOT EXISTS idx_v03_policy ON orders(o_clerk);

-- 3. Enable Row Level Security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 4. Create the Inline Policy (Hardcoded Clerk)
CREATE POLICY inline_policy_v03 
ON orders 
FOR SELECT 
TO rls_tester 
USING (o_clerk = 'Clerk#000000001');