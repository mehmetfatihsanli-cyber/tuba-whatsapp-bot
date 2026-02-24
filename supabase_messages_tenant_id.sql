-- Panel güvenliği: Her mağazanın sadece kendi mesajlarını görmesi için tenant_id eklenir.
-- Supabase SQL Editor'da çalıştır.

-- Sütun ekle (mevcut kayıtlar 'tuba' olur)
ALTER TABLE public.messages
ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'tuba';

-- Eski kayıtları güncelle (tenant_id NULL ise)
UPDATE public.messages SET tenant_id = 'tuba' WHERE tenant_id IS NULL;

-- İndeks (tenant'a göre filtre hızlı olsun)
CREATE INDEX IF NOT EXISTS idx_messages_tenant_id ON public.messages (tenant_id);

COMMENT ON COLUMN public.messages.tenant_id IS 'Mağaza: tuba, zafer, ali - panelde sadece kendi mesajları gösterilir';
