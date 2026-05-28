-- ==============================================================================
-- V07 SETUP: Huge Table | Table Policy | Query INDEXED | Policy UNINDEXED (Multi-Row)
-- ==============================================================================

-- 1. Create a dedicated least-privilege role for testing
DROP ROLE IF EXISTS rls_tester;
CREATE ROLE rls_tester LOGIN PASSWORD 'rls_tester_password';
GRANT USAGE ON SCHEMA public TO rls_tester;
GRANT SELECT ON lineitem TO rls_tester;

-- 2. Create the mapping table for Supplier Isolation
DROP TABLE IF EXISTS rls_mapping;
CREATE TABLE rls_mapping (
    db_user TEXT,
    supp_key INT
);
-- Hardcode the test supplier mapping for the tester role (e.g., Supplier #2346)
INSERT INTO rls_mapping (db_user, supp_key) VALUES ('rls_tester', 2346);
GRANT SELECT ON rls_mapping TO rls_tester;

-- 3. Create index for V07 (Only Query predicate indexed on the massive lineitem table)
CREATE INDEX IF NOT EXISTS idx_lineitem_partkey ON lineitem(l_partkey);
-- Note: We DO NOT create an index on l_suppkey for this variation.

-- 4. Enable Row Level Security
ALTER TABLE lineitem ENABLE ROW LEVEL SECURITY;

-- 5. Create the Table-based Policy
CREATE POLICY table_policy_v07 
ON lineitem 
FOR SELECT 
TO rls_tester 
USING (l_suppkey IN (SELECT supp_key FROM rls_mapping WHERE db_user = current_user));

-- 6. Force statistics update to ensure query planner awareness
ANALYZE lineitem;
ANALYZE rls_mapping;