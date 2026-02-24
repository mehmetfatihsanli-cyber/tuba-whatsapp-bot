-- Satış hattı / Değişim hattı: numaraya göre ayrım. Panelde ve modelde satış vs değişim davranışı.

-- 1. Tenants: değişim hattı için ayrı numara ve token (opsiyonel)
ALTER TABLE public.tenants
  ADD COLUMN IF NOT EXISTS whatsapp_phone_number_id_exchange TEXT,
  ADD COLUMN IF NOT EXISTS whatsapp_access_token_exchange TEXT;
COMMENT ON COLUMN public.tenants.whatsapp_phone_number_id_exchange IS 'Değişim/İade hattı WhatsApp Phone Number ID';
COMMENT ON COLUMN public.tenants.whatsapp_access_token_exchange IS 'Değişim hattı Meta Access Token';

-- 2. Messages: hangi hattan geldiği (satış numarası -> sales, değişim numarası -> exchange)
ALTER TABLE public.messages
  ADD COLUMN IF NOT EXISTS line TEXT NOT NULL DEFAULT 'sales';
COMMENT ON COLUMN public.messages.line IS 'sales = satış hattı, exchange = değişim/iade hattı';

-- 3. Customers: müşteri hangi hatta (aynı telefon iki hatta ayrı görünsün)
ALTER TABLE public.customers
  ADD COLUMN IF NOT EXISTS line TEXT NOT NULL DEFAULT 'sales';
COMMENT ON COLUMN public.customers.line IS 'sales = satış hattı, exchange = değişim/iade hattı';

-- Not: Aynı tenant + phone iki hattta ayrı görünsün diye (tenant_id, phone, line) unique yapılabilir.
-- Eski unique (tenant_id, phone) varsa kaldırılmalı: ALTER TABLE customers DROP CONSTRAINT ...;
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_tenant_phone_line ON public.customers (tenant_id, phone, line);
