-- Hepsiburada ve N11 pazaryeri entegrasyonu için tenants tablosuna sütunlar
-- Supabase SQL Editor'da çalıştır. Mevcut tabloya sütun ekler.

ALTER TABLE public.tenants
  ADD COLUMN IF NOT EXISTS hepsiburada_seller_id TEXT,
  ADD COLUMN IF NOT EXISTS hepsiburada_api_key TEXT,
  ADD COLUMN IF NOT EXISTS hepsiburada_api_secret TEXT,
  ADD COLUMN IF NOT EXISTS n11_seller_id TEXT,
  ADD COLUMN IF NOT EXISTS n11_api_key TEXT,
  ADD COLUMN IF NOT EXISTS n11_api_secret TEXT;

COMMENT ON COLUMN public.tenants.hepsiburada_seller_id IS 'Hepsiburada Satıcı ID';
COMMENT ON COLUMN public.tenants.hepsiburada_api_key IS 'Hepsiburada API Key';
COMMENT ON COLUMN public.tenants.hepsiburada_api_secret IS 'Hepsiburada API Secret (gizli)';
COMMENT ON COLUMN public.tenants.n11_seller_id IS 'N11 Satıcı ID';
COMMENT ON COLUMN public.tenants.n11_api_key IS 'N11 API Key';
COMMENT ON COLUMN public.tenants.n11_api_secret IS 'N11 API Secret (gizli)';
