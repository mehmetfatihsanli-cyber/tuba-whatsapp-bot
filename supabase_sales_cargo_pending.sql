-- Satış: sipariş bilgisi beklenen müşteriler (Supabase MCP ile uygulandı: add_sales_cargo_pending)
-- Değişim tarafı ayrı; bu tablo sadece satış (WhatsApp sipariş) için.

CREATE TABLE IF NOT EXISTS public.sales_cargo_pending (
  tenant_id TEXT NOT NULL,
  phone TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (tenant_id, phone)
);

COMMENT ON TABLE public.sales_cargo_pending IS 'Satış: müşteri sipariş vermek istedi, kargo bilgisi bekleniyor';
