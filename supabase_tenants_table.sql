-- ============================================================
-- TENANTS TABLOSU - Çok kiracılı marka (company_name, logo_url)
-- Supabase SQL Editor'da bir kez çalıştır.
-- Eski "tenants" tablosu farklı yapıdaysa once silinir, sonra dogru yapiyla olusturulur.
-- ============================================================

DROP TABLE IF EXISTS public.tenants CASCADE;

CREATE TABLE public.tenants (
  tenant_id TEXT PRIMARY KEY,
  company_name TEXT NOT NULL,
  logo_url TEXT
);

-- Varsayılan değerler (Tuba, Zafer, Ali)
INSERT INTO public.tenants (tenant_id, company_name, logo_url) VALUES
  ('tuba', 'Tuba Butik', NULL),
  ('zafer', 'Zafer Giyim', NULL),
  ('ali', 'Ali', NULL)
ON CONFLICT (tenant_id) DO NOTHING;

COMMENT ON TABLE public.tenants IS 'Panel sol ust marka: company_name ve logo_url dinamik gosterilir';
