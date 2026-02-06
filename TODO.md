# ⚠️ KRİTİK YAPILACAKLAR LİSTESİ - UNUTMA!

## 🔴 ACİL (Claude API Eklenir Eklenmez - MUTLAKA YAP!)

### 1. COST CAP (Maliyet Limiti) - KRİTİK! 💰
**Risk:** Fatura patlar, batarsın!
**Durum:** ❌ YAPILMADI
**Tetikleyici:** Claude API key eklediğinde ÖNCE BUNU YAP!

### 2. RATE LIMITING (Spam Koruması) - KRİTİK! 🛡️
**Risk:** Saldırı olursa sistem çöker!
**Durum:** ❌ YAPILMADI
**Tetikleyici:** Claude API key eklediğinde ÖNCE BUNU YAP!

### 3. ERROR LOGGING (Hata Kayıt) - ÖNEMLİ! 📝
**Risk:** Hata olunca ne olduğunu bilemezsin!
**Durum:** ❌ YAPILMADI
**Tetikleyici:** Claude API key eklediğinde ÖNCE BUNU YAP!

---

## 🟡 ORTA ÖNCELİK (2. Müşteri Eklerken - MUTLAKA YAP!)

### 4. RLS (Row Level Security) - KRİTİK! 🔐
**Risk:** Tuba, Zafer'in verilerini görebilir!
**Durum:** ❌ YAPILMADI
**Tetikleyici:** 2. müşteri (Zafer) eklenirken ÖNCE BUNU YAP!

### 5. KVKK AYDINLATMA METNİ - ZORUNLU! ⚖️
**Risk:** Dava riski, ceza 2M TL!
**Durum:** ❌ YAPILMADI
**Tetikleyici:** Tuba canlıya geçmeden ÖNCE BUNU YAP!

---

## 🟢 DÜŞÜK ÖNCELİK (3+ Müşteri Olunca)

### 6. CLI ADMIN TOOL (admin.py) - KOLAYLIK
**Risk:** Yok, sadece kolaylık
**Durum:** ❌ YAPILMADI
**Tetikleyici:** 3+ müşteri olunca veya ihtiyaç duyunca

---

## ✅ KONTROL LİSTESİ

| # | Konu | Öncelik | Durum | Ne Zaman? |
|---|------|---------|-------|-----------|
| 1 | Cost Cap | 🔴 Acil | ❌ | Claude API key eklenince |
| 2 | Rate Limiting | 🔴 Acil | ❌ | Claude API key eklenince |
| 3 | Error Logging | 🔴 Acil | ❌ | Claude API key eklenince |
| 4 | RLS Security | 🟡 Orta | ❌ | 2. müşteri eklenince |
| 5 | KVKK Metni | 🟡 Orta | ❌ | Canlıya geçmeden önce |
| 6 | Admin Tool | 🟢 Düşük | ❌ | 3+ müşteri olunca |

---

## 🚨 TETİKLEYİCİLER - BU DURUMLARDA BU DOSYAYI AÇ!

### ⚡ Tetikleyici 1: Claude API Key Ekliyorsun
```
🛑 DURMA! TODO.md dosyasını aç!
📋 Madde 1, 2, 3'ü yap!
```

### ⚡ Tetikleyici 2: 2. Müşteri (Zafer) Ekliyorsun
```
🛑 DURMA! TODO.md dosyasını aç!
📋 Madde 4'ü yap (RLS)!
```

### ⚡ Tetikleyici 3: Tuba Canlıya Geçiyor
```
🛑 DURMA! TODO.md dosyasını aç!
📋 Madde 5'i yap (KVKK)!
```

---

**Son Güncelleme:** 02 Şubat 2026
**Her gün kontrol et!** ✅

---

# 📊 SUPABASE VERİTABANI ŞEMASI

## TABLO 1: tenants (Müşteriler)
```sql
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  whatsapp_phone_id TEXT UNIQUE NOT NULL,
  
  -- Modül kontrolü (Aç/Kapa)
  modules JSONB DEFAULT '{
    "sales_assistant": false,
    "return_exchange": false,
    "order_tracking": false
  }',
  
  -- Entegrasyonlar (Butik, İkas API keys)
  integrations JSONB DEFAULT '{}',
  
  -- Özel kurallar
  system_prompt_rules TEXT,
  
  -- Maliyet limiti (Cost Cap için)
  monthly_usage_limit DECIMAL DEFAULT 50.00,
  current_month_usage DECIMAL DEFAULT 0.00,
  
  -- Sahibin telefonu (Bildirimler için)
  owner_phone TEXT,
  owner_email TEXT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## TABLO 2: conversations (Konuşmalar)
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES tenants(id),
  customer_phone TEXT NOT NULL,
  
  message_type TEXT, -- 'text', 'image'
  message_content TEXT,
  
  ai_response TEXT,
  module_used TEXT, -- 'sales_assistant', 'return_exchange', 'missed_opportunity'
  
  processing_time_ms INTEGER,
  cost DECIMAL, -- Claude API maliyeti
  
  error_message TEXT,
  image_url TEXT,
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- Index (Hızlı sorgular için)
CREATE INDEX idx_conversations_tenant ON conversations(tenant_id);
CREATE INDEX idx_conversations_phone ON conversations(customer_phone);
CREATE INDEX idx_conversations_date ON conversations(created_at);
```

## TABLO 3: usage_tracking (Maliyet Takibi)
```sql
CREATE TABLE usage_tracking (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES tenants(id),
  
  month TEXT, -- '2026-02'
  total_messages INTEGER DEFAULT 0,
  total_cost DECIMAL DEFAULT 0.00,
  
  PRIMARY KEY (tenant_id, month)
);
```

## RLS (Row Level Security) - 2. Müşteri Eklenince YAP!
```sql
-- Her tenant sadece kendi verilerini görsün
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenants see own data" ON tenants
  FOR ALL USING (id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY "Tenants see own conversations" ON conversations
  FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

---

## ✅ SUPABASE KURULUM KONTROL LİSTESİ

- [ ] Supabase hesabı oluştur
- [ ] `tenants` tablosu oluştur
- [ ] `conversations` tablosu oluştur  
- [ ] `usage_tracking` tablosu oluştur
- [ ] Index'leri ekle
- [ ] RLS'i kur (2. müşteri eklenince!)
- [ ] URL ve Key'i `.env` dosyasına ekle

