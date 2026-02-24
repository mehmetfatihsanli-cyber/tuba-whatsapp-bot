-- Satış Hunisi (Pipeline): müşteri aşaması ve etiketler
-- Proje: tuba-whatsapp-bot | Supabase MCP ile uygulandı: add_customers_status_for_pipeline

ALTER TABLE public.customers
ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'new';

COMMENT ON COLUMN public.customers.status IS 'Satış hunisi: new, interested, negotiation, won';

ALTER TABLE public.customers
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT NULL;

COMMENT ON COLUMN public.customers.tags IS 'Opsiyonel etiketler: VIP, Acele vb.';
