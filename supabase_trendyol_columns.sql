-- Trendyol pazaryeri entegrasyonu için tenants tablosuna sütunlar
-- Supabase SQL Editor'da çalıştır. Mevcut tabloya sütun ekler.

ALTER TABLE public.tenants
  ADD COLUMN IF NOT EXISTS trendyol_seller_id TEXT,
  ADD COLUMN IF NOT EXISTS trendyol_api_key TEXT,
  ADD COLUMN IF NOT EXISTS trendyol_api_secret TEXT;

COMMENT ON COLUMN public.tenants.trendyol_seller_id IS 'Trendyol Satıcı ID (Seller ID)';
COMMENT ON COLUMN public.tenants.trendyol_api_key IS 'Trendyol API Key';
COMMENT ON COLUMN public.tenants.trendyol_api_secret IS 'Trendyol API Secret (gizli tutulur)';
