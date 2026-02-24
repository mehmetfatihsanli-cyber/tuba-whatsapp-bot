-- Değişim: kargo onayı beklenen müşteriler. Adres son siparişten; "farklı adres" derse parsed_data dolu.

CREATE TABLE IF NOT EXISTS public.exchange_cargo_pending (
  tenant_id TEXT NOT NULL,
  phone TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  parsed_data JSONB,
  PRIMARY KEY (tenant_id, phone)
);

COMMENT ON TABLE public.exchange_cargo_pending IS 'Değişim: müşteri kargo onayı bekleniyor; parsed_data null = son sipariş adresi, dolu = yeni adres';
