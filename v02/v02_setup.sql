-- ==============================================================================
-- V02 SETUP: Large Table | Inline Policy | Query Indexed | Policy UNINDEXED
-- ==============================================================================

-- 1. Create a dedicated least-privilege role for testing
DROP ROLE IF EXISTS rls_tester;
CREATE ROLE rls_tester LOGIN;
GRANT USAGE ON SCHEMA public TO rls_tester;
GRANT SELECT ON orders TO rls_tester;

-- Note: We DO NOT create an index on o_clerk for this variation.
-- We rely solely on the implicit PK index for o_orderkey (Query Predicate).

-- 2. Enable Row Level Security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 3. Create the Inline Policy
CREATE POLICY inline_policy_v02 
ON orders 
FOR SELECT 
TO rls_tester 
USING (o_clerk = current_setting('rls.test_clerk', true));