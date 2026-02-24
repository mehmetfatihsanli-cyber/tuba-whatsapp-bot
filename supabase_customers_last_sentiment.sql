-- Duygusal zeka: son analiz (Supabase MCP ile uygulandı: add_customers_last_sentiment)
ALTER TABLE public.customers
ADD COLUMN IF NOT EXISTS last_sentiment TEXT DEFAULT NULL;

COMMENT ON COLUMN public.customers.last_sentiment IS 'Son duygu: positive, neutral, negative, angry (Claude analizi)';
