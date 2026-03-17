-- Migration script for existing installations (create_all -> assignment schema)
-- Adds required columns and backfills where possible.

BEGIN;

-- Vendors: add contact + rating
ALTER TABLE vendors
  ADD COLUMN IF NOT EXISTS contact VARCHAR(200),
  ADD COLUMN IF NOT EXISTS rating NUMERIC(2,1) NOT NULL DEFAULT 0.0;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_vendors_rating_0_5'
  ) THEN
    ALTER TABLE vendors
      ADD CONSTRAINT ck_vendors_rating_0_5 CHECK (rating >= 0 AND rating <= 5);
  END IF;
END $$;

-- Products: add stock_level
ALTER TABLE products
  ADD COLUMN IF NOT EXISTS stock_level INTEGER NOT NULL DEFAULT 0;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_products_stock_level_non_negative'
  ) THEN
    ALTER TABLE products
      ADD CONSTRAINT ck_products_stock_level_non_negative CHECK (stock_level >= 0);
  END IF;
END $$;

-- Purchase Orders: add reference_no + status + total_amount
ALTER TABLE purchase_orders
  ADD COLUMN IF NOT EXISTS reference_no VARCHAR(32),
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
  ADD COLUMN IF NOT EXISTS total_amount NUMERIC(14,2);

-- Backfill total_amount from old 'total' column if present
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name='purchase_orders' AND column_name='total'
  ) THEN
    UPDATE purchase_orders SET total_amount = total WHERE total_amount IS NULL;
  END IF;
END $$;

-- Drop legacy 'total' column (was NOT NULL in older schema and breaks inserts)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name='purchase_orders' AND column_name='total'
  ) THEN
    ALTER TABLE purchase_orders DROP COLUMN total;
  END IF;
END $$;

-- Backfill reference_no using id
UPDATE purchase_orders
SET reference_no = CONCAT('PO-', EXTRACT(YEAR FROM NOW())::INT, '-', LPAD(id::TEXT, 6, '0'))
WHERE reference_no IS NULL;

-- Ensure reference_no and total_amount are not null
ALTER TABLE purchase_orders
  ALTER COLUMN reference_no SET NOT NULL,
  ALTER COLUMN total_amount SET NOT NULL;

-- Add unique constraint/index for reference_no if missing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes WHERE indexname = 'ix_purchase_orders_reference_no'
  ) THEN
    CREATE UNIQUE INDEX ix_purchase_orders_reference_no ON purchase_orders(reference_no);
  END IF;
END $$;

COMMIT;

