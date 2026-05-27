-- ==============================================================================
-- V05 TEARDOWN: Clean up structures created for V05
-- ==============================================================================

-- 1. Drop the policy and disable RLS
DROP POLICY IF EXISTS table_policy_v05 ON orders;
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;

-- 2. Drop the indexes
DROP INDEX IF EXISTS idx_orders_totalprice;
DROP INDEX IF EXISTS idx_orders_clerk;

-- 3. Drop the mapping table
REVOKE SELECT ON rls_mapping FROM rls_tester;
DROP TABLE IF EXISTS rls_mapping;

-- 4. Revoke permissions and drop the test role
REVOKE SELECT ON orders FROM rls_tester;
REVOKE USAGE ON SCHEMA public FROM rls_tester;
DROP ROLE IF EXISTS rls_tester;