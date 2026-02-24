-- 1) Panel: messages tablosuna tenant_id (Tuba/Zafer/Ali ayrımı)
ALTER TABLE public.messages
ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'tuba';

UPDATE public.messages SET tenant_id = 'tuba' WHERE tenant_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_messages_tenant_id ON public.messages (tenant_id);

-- 2) Yeni müşteri: Her gelen müşteri için tek kayıt (tenant + telefon başına bir kez)
CREATE TABLE IF NOT EXISTS public.customers (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  phone TEXT NOT NULL,
  first_seen_at TIMESTAMPTZ DEFAULT NOW(),
  last_message_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(tenant_id, phone)
);

CREATE INDEX IF NOT EXISTS idx_customers_tenant_phone ON public.customers (tenant_id, phone);
CREATE INDEX IF NOT EXISTS idx_customers_first_seen ON public.customers (first_seen_at DESC);

COMMENT ON TABLE public.customers IS 'İlk kez mesaj atan müşteriler - yeni müşteri açıldı bilgisi';
