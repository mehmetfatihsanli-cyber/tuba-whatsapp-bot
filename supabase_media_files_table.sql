-- AI Stüdyo / Görsel Sihirbazı için placeholder tablo.
-- İleride "360° ürün görseli" özelliği eklendiğinde kullanılacak.
-- Şu an tabloyu oluşturuyoruz; uygulama içinde aktif kullanım yok.

CREATE TABLE IF NOT EXISTS media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    original_image_url TEXT,
    processed_360_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'published')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- İsteğe bağlı: updated_at otomatik güncelleme
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS media_files_updated_at ON media_files;
CREATE TRIGGER media_files_updated_at
    BEFORE UPDATE ON media_files
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at();

COMMENT ON TABLE media_files IS 'AI Stüdyo: ürün fotoğrafı -> 360 görsel (placeholder, henüz aktif kullanılmıyor)';
