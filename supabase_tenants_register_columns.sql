-- Kayıt (Register) için tenants tablosuna e-posta ve şifre alanları
-- Supabase SQL Editor'da çalıştır. Mevcut tuba/zafer/ali satırları etkilenmez (email/password_hash NULL kalır).

ALTER TABLE public.tenants
  ADD COLUMN IF NOT EXISTS email TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS password_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_tenants_email ON public.tenants (email) WHERE email IS NOT NULL;
COMMENT ON COLUMN public.tenants.email IS 'Kayıt olan mağaza e-postası; girişte kullanılır';
COMMENT ON COLUMN public.tenants.password_hash IS 'Werkzeug ile hashlenmiş şifre';
