-- ==============================================================================
-- V06 SETUP: Large Table | Table Policy | Query INDEXED | Policy UNINDEXED
-- ==============================================================================

-- 1. Create a dedicated least-privilege role for testing
DROP ROLE IF EXISTS rls_tester;
CREATE ROLE rls_tester LOGIN PASSWORD 'rls_tester_password';
GRANT USAGE ON SCHEMA public TO rls_tester;
GRANT SELECT ON orders TO rls_tester;

-- 2. Create the mapping table to avoid SET commands
DROP TABLE IF EXISTS rls_mapping;
CREATE TABLE rls_mapping (
    db_user TEXT,
    clerk_id TEXT
);
-- Hardcode the test clerk mapping for the tester role
INSERT INTO rls_mapping (db_user, clerk_id) VALUES ('rls_tester', 'Clerk#000000001');
GRANT SELECT ON rls_mapping TO rls_tester;

-- 3. Create index for V06 (Only Query predicate indexed)
CREATE INDEX IF NOT EXISTS idx_orders_totalprice ON orders(o_totalprice);
-- Note: We DO NOT create an index on o_clerk for this variation.

-- 4. Enable Row Level Security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 5. Create the Table-based Policy
CREATE POLICY table_policy_v06 
ON orders 
FOR SELECT 
TO rls_tester 
USING (o_clerk IN (SELECT clerk_id FROM rls_mapping WHERE db_user = current_user));

ANALYZE orders;
ANALYZE rls_mapping;
