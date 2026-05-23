-- ==============================================================================
-- V02 SETUP: Large Table | Inline Policy | Query Indexed | Policy UNINDEXED
-- ==============================================================================

-- 1. Create a dedicated least-privilege role for testing
DROP ROLE IF EXISTS rls_tester;
CREATE ROLE rls_tester LOGIN PASSWORD 'rls_tester_password';
GRANT USAGE ON SCHEMA public TO rls_tester;
GRANT SELECT ON orders TO rls_tester;

-- Note: No index is created for o_clerk for this variation.

-- 2. Enable Row Level Security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 3. Create the Inline Policy (Hardcoded Clerk)
CREATE POLICY inline_policy_v02 
ON orders 
FOR SELECT 
TO rls_tester 
USING (o_clerk = 'Clerk#000000001');