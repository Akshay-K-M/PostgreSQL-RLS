-- clean_tpch.sql
-- 1. Wipe out any RLS policies you might have created so they don't mess with future plans
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    FOR r IN (SELECT table_name FROM information_schema.tables WHERE table_schema = 'public') LOOP
        EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY;', r.table_name);
    END LOOP;
END $$;

-- 2. Empty the tables completely (preserves your schema structure)
TRUNCATE TABLE customer, orders, lineitem, nation, region, part, supplier, partsupp CASCADE;

-- duckdb -c "
-- INSTALL postgres;
-- LOAD postgres;
-- -- 1. Install and load the missing TPC-H generator extension
-- INSTALL tpch;
-- LOAD tpch;

-- -- 2. Connect to your Postgres instance 
-- ATTACH 'dbname=tpch user=username host=localhost' AS pg (TYPE POSTGRES);

-- -- 3. Use the correct dbgen functions with Scale Factor 1 specified
-- INSERT INTO pg.public.nation   SELECT * FROM dbgen(sf=1, children=25) WHERE table_name='nation';
-- INSERT INTO pg.public.region   SELECT * FROM dbgen(sf=1, children=5)  WHERE table_name='region';
-- INSERT INTO pg.public.part     SELECT * FROM dbgen(sf=1) WHERE table_name='part';
-- INSERT INTO pg.public.supplier SELECT * FROM dbgen(sf=1) WHERE table_name='supplier';
-- INSERT INTO pg.public.partsupp SELECT * FROM dbgen(sf=1) WHERE table_name='partsupp';
-- INSERT INTO pg.public.customer SELECT * FROM dbgen(sf=1) WHERE table_name='customer';
-- INSERT INTO pg.public.orders   SELECT * FROM dbgen(sf=1) WHERE table_name='orders';
-- INSERT INTO pg.public.lineitem SELECT * FROM dbgen(sf=1) WHERE table_name='lineitem';
-- "