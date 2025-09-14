SCHEMA_QUERY = """
    SELECT 
        c.relname as table_name,
        a.attname as column_name,
        format_type(a.atttypid, a.atttypmod) as data_type
    FROM 
        pg_class c
    JOIN 
        pg_namespace n ON n.oid = c.relnamespace
    JOIN 
        pg_attribute a ON a.attrelid = c.oid
    LEFT JOIN 
        pg_attrdef ad ON (a.attrelid = ad.adrelid AND a.attnum = ad.adnum)
    WHERE 
        n.nspname = $1  -- Replace with your schema name
        AND c.relkind = 'r'             -- Only regular tables
        AND a.attnum > 0                -- Exclude system columns
        AND NOT a.attisdropped          -- Exclude dropped columns
    ORDER BY 
        c.relname, 
        a.attnum;
    """