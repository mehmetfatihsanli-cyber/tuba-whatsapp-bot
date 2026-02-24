-- Hat bazlı bot modu: Satış ve Değişim ayrı ayrı (Canlı / Dinle+Analiz / Kapat)
-- Genel Bakış panelinde her kart için 3 buton: Canlı | Dinle + Analiz | Kapat

ALTER TABLE public.tenants
ADD COLUMN IF NOT EXISTS bot_mode_sales TEXT DEFAULT 'live',
ADD COLUMN IF NOT EXISTS bot_mode_exchange TEXT DEFAULT 'live';

COMMENT ON COLUMN public.tenants.bot_mode_sales IS 'sales hattı: live, listen_analyze, off';
COMMENT ON COLUMN public.tenants.bot_mode_exchange IS 'exchange hattı: live, listen_analyze, off';

-- Dinle+Analiz döneminde her mesaj için analiz kaydı (Analiz Raporu sayfasında gösterilir)
CREATE TABLE IF NOT EXISTS public.message_analyses (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    phone TEXT NOT NULL,
    line TEXT NOT NULL,
    message_body TEXT,
    sentiment TEXT,
    intent TEXT,
    urgency TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_message_analyses_tenant_created ON public.message_analyses(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_message_analyses_line ON public.message_analyses(tenant_id, line, created_at DESC);

COMMENT ON TABLE public.message_analyses IS 'Dinle+Analiz modunda AI analiz sonuçları; Analiz Raporu sayfasında listelenir';
