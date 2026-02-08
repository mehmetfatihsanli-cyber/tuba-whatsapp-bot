-- Tuba WhatsApp Bot - messages tablosu
-- Supabase Dashboard -> SQL Editor'a yapıştırıp "Run" ile çalıştır.

CREATE TABLE IF NOT EXISTS public.messages (
  id BIGSERIAL PRIMARY KEY,
  phone TEXT NOT NULL,
  message_body TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- İsteğe bağlı: created_at ile hızlı sıralama
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_phone ON public.messages (phone);

COMMENT ON TABLE public.messages IS 'WhatsApp gelen/giden mesaj logu - Tuba Bot';
