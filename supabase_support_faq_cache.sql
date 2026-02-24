-- support_faq_cache: Web sitesi chatbot'unda aynı soru tekrar gelince token harcanmaması için cevap hafızası.
-- Supabase Dashboard -> SQL Editor -> bu dosyanın tümünü yapıştır -> Run.

CREATE TABLE IF NOT EXISTS public.support_faq_cache (
  context TEXT NOT NULL DEFAULT 'website',
  question_normalized TEXT NOT NULL,
  reply TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (context, question_normalized)
);

CREATE INDEX IF NOT EXISTS idx_support_faq_cache_lookup
  ON public.support_faq_cache (context, question_normalized);

COMMENT ON TABLE public.support_faq_cache IS 'Website support chat: ilk soruda Claude cevabı saklanır, aynı soru tekrar gelince cache''den döner (token tasarrufu).';
