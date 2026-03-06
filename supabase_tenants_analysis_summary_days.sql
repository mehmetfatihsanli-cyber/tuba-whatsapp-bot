-- Analiz özeti penceresi (gün): Panelde seçilen 2/7/14 gün hem rapor hem modele giden özet için kullanılır.
-- Supabase SQL Editor'da bir kez çalıştır.

ALTER TABLE public.tenants
ADD COLUMN IF NOT EXISTS analysis_summary_days integer DEFAULT 2;

COMMENT ON COLUMN public.tenants.analysis_summary_days IS 'Modele giden analiz özeti ve rapor varsayılan penceresi: 2, 7 veya 14 gün';
