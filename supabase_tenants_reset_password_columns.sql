-- Şifre sıfırlama (Forgot Password) için tenants tablosuna sütunlar
-- Supabase SQL Editor'da bir kez çalıştır.

ALTER TABLE public.tenants
  ADD COLUMN IF NOT EXISTS reset_token TEXT,
  ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMPTZ;

COMMENT ON COLUMN public.tenants.reset_token IS 'Şifre sıfırlama linki için tek kullanımlık token';
COMMENT ON COLUMN public.tenants.reset_token_expires IS 'Token geçerlilik süresi (örn. 1 saat)';
