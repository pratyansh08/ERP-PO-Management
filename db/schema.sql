-- Purchase Order Management System - Schema (PostgreSQL)
-- This schema matches the assignment's required columns:
-- Vendors(Name, Contact, Rating), Products(Name, SKU, Unit Price, Stock Level),
-- PurchaseOrders(Reference No, VendorID, Total Amount, Status) + items table for line items.

BEGIN;

CREATE TABLE IF NOT EXISTS vendors (
  id           BIGSERIAL PRIMARY KEY,
  name         VARCHAR(200) NOT NULL UNIQUE,
  contact      VARCHAR(200),
  rating       NUMERIC(2,1) NOT NULL DEFAULT 0.0,
  email        VARCHAR(254) UNIQUE,
  phone        VARCHAR(50),
  address      VARCHAR(500),
  CONSTRAINT ck_vendors_rating_0_5 CHECK (rating >= 0 AND rating <= 5)
);

CREATE TABLE IF NOT EXISTS products (
  id           BIGSERIAL PRIMARY KEY,
  sku          VARCHAR(64) NOT NULL UNIQUE,
  name         VARCHAR(200) NOT NULL,
  price        NUMERIC(12,2) NOT NULL,
  stock_level  INTEGER NOT NULL DEFAULT 0,
  CONSTRAINT ck_products_stock_level_non_negative CHECK (stock_level >= 0)
);

CREATE TABLE IF NOT EXISTS purchase_orders (
  id            BIGSERIAL PRIMARY KEY,
  reference_no  VARCHAR(32) NOT NULL UNIQUE,
  vendor_id     BIGINT NOT NULL REFERENCES vendors(id) ON DELETE RESTRICT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  subtotal      NUMERIC(14,2) NOT NULL,
  tax           NUMERIC(14,2) NOT NULL,
  total_amount  NUMERIC(14,2) NOT NULL,
  status        VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
);

CREATE INDEX IF NOT EXISTS ix_purchase_orders_vendor_id ON purchase_orders(vendor_id);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_status ON purchase_orders(status);

CREATE TABLE IF NOT EXISTS purchase_order_items (
  id                 BIGSERIAL PRIMARY KEY,
  purchase_order_id  BIGINT NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
  product_id         BIGINT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
  quantity           INTEGER NOT NULL,
  unit_price         NUMERIC(12,2) NOT NULL,
  line_total         NUMERIC(14,2) NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_purchase_order_items_po_id ON purchase_order_items(purchase_order_id);
CREATE INDEX IF NOT EXISTS ix_purchase_order_items_product_id ON purchase_order_items(product_id);

COMMIT;

