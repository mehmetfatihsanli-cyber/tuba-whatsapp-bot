-- ============================================================
-- RLS (Row Level Security) Açma - Tuba WhatsApp Bot
-- Supabase Dashboard -> SQL Editor'a yapıştırıp "Run" ile çalıştır.
-- ============================================================
-- Bu script tüm ilgili tablolarda RLS'i açar.
-- Backend (Flask) SUPABASE_KEY ile service_role kullandığı için
-- RLS'ten muaf kalır; test mesajları ve mevcut akış çalışmaya devam eder.
-- Anon/authenticated ile doğrudan tabloya erişim kısıtlanır (güvenlik).
-- ============================================================

-- 1. tenants
ALTER TABLE IF EXISTS public.tenants ENABLE ROW LEVEL SECURITY;

-- 2. messages
ALTER TABLE IF EXISTS public.messages ENABLE ROW LEVEL SECURITY;

-- 3. customers
ALTER TABLE IF EXISTS public.customers ENABLE ROW LEVEL SECURITY;

-- 4. conversation_state
ALTER TABLE IF EXISTS public.conversation_state ENABLE ROW LEVEL SECURITY;

-- 5. media_files (varsa; yoksa hata vermez)
ALTER TABLE IF EXISTS public.media_files ENABLE ROW LEVEL SECURITY;

-- 6. conversations (projede kullanılmıyor; eski/kopya tablo - RLS yine açık olsun)
ALTER TABLE IF EXISTS public.conversations ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Opsiyonel: Service role dışında kimse erişemesin (varsayılan zaten bu).
-- Ek politika gerekmez; policy yok = sadece service_role erişir.
-- İleride panelden anon key ile erişim istersen, tenant bazlı policy eklenir.
-- ============================================================

COMMENT ON TABLE public.tenants IS 'RLS açık; backend service_role ile erişir';
COMMENT ON TABLE public.messages IS 'RLS açık; backend service_role ile erişir';
COMMENT ON TABLE public.customers IS 'RLS açık; backend service_role ile erişir';
COMMENT ON TABLE public.conversation_state IS 'RLS açık; backend service_role ile erişir';
