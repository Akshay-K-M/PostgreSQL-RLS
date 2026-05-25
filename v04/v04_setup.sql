-- ==============================================================================
-- V04 SETUP: Large Table | Inline Policy | Query UNINDEXED | Policy UNINDEXED
-- ==============================================================================

-- 1. Create a dedicated least-privilege role for testing
DROP ROLE IF EXISTS rls_tester;
CREATE ROLE rls_tester LOGIN PASSWORD 'rls_tester_password';
GRANT USAGE ON SCHEMA public TO rls_tester;
GRANT SELECT ON orders TO rls_tester;

-- Note: We DO NOT create an index on o_clerk for this variation.
-- We are also querying by o_totalprice, which has no index.

-- 2. Enable Row Level Security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 3. Create the Inline Policy (Hardcoded Clerk)
CREATE POLICY inline_policy_v04 
ON orders 
FOR SELECT 
TO rls_tester 
USING (o_clerk = 'Clerk#000000001');