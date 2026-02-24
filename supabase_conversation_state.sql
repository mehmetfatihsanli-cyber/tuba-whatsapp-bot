-- conversation_state: Bot yetkiliye yönlendirdiğinde panelde hangi numaraların uyarı alacağını tutar.
-- Supabase Dashboard -> SQL Editor -> bu dosyanın tümünü yapıştır -> Run.

CREATE TABLE IF NOT EXISTS public.conversation_state (
  tenant_id TEXT NOT NULL,
  phone TEXT NOT NULL,
  handoff_requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (tenant_id, phone)
);

CREATE INDEX IF NOT EXISTS idx_conversation_state_tenant ON public.conversation_state (tenant_id);
