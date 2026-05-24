-- ==============================================================================
-- V03 TEARDOWN: Clean up structures created for V03
-- ==============================================================================

-- 1. Drop the policy and disable RLS
DROP POLICY IF EXISTS inline_policy_v03 ON orders;
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;

-- 2. Drop the explicit policy index
DROP INDEX IF EXISTS idx_v03_policy;

-- 3. Revoke permissions and drop the test role
REVOKE SELECT ON orders FROM rls_tester;
REVOKE USAGE ON SCHEMA public FROM rls_tester;
DROP ROLE IF EXISTS rls_tester;