-- Bot modu: live (cevap ver), listen (sadece dinle), listen_analyze (dinle + analiz et, cevap verme)
-- Panelden "Bot modu" seçeneği ile canlıya geçmeden önce dinleme/analiz modunda test için kullanılır.
ALTER TABLE public.tenants
ADD COLUMN IF NOT EXISTS bot_mode TEXT DEFAULT 'live';

COMMENT ON COLUMN public.tenants.bot_mode IS 'live = bot cevap verir, listen = sadece mesaj kaydedilir, listen_analyze = AI analiz eder ama cevap gönderilmez';
