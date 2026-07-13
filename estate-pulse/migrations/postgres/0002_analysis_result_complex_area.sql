ALTER TABLE analysis_result ALTER COLUMN listing_id DROP NOT NULL;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS target_type TEXT NOT NULL DEFAULT 'LISTING';

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS complex_id BIGINT;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS area_bucket DOUBLE PRECISION;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS price_source TEXT;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS effective_price_snapshot BIGINT;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS reference_price BIGINT;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS sample_count BIGINT;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS latest_transaction_date TEXT;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS selected_transaction_min_price BIGINT;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS selected_transaction_max_price BIGINT;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS confidence TEXT;

ALTER TABLE analysis_result
    ADD COLUMN IF NOT EXISTS volatility_status TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'analysis_result_complex_id_fkey'
          AND table_name = 'analysis_result'
    ) THEN
        ALTER TABLE analysis_result
            ADD CONSTRAINT analysis_result_complex_id_fkey
            FOREIGN KEY (complex_id) REFERENCES apartment_complex(id) ON DELETE CASCADE;
    END IF;
END
$$;
