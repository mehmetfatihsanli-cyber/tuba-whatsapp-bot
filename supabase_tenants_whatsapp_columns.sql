-- tenants tablosuna WhatsApp kurulum alanları (WhatsApp Entegrasyon Sihirbazı için)
-- Supabase SQL Editor'da çalıştır. Mevcut tabloya sütun ekler.

ALTER TABLE public.tenants
  ADD COLUMN IF NOT EXISTS whatsapp_phone_number_id TEXT,
  ADD COLUMN IF NOT EXISTS whatsapp_waba_id TEXT,
  ADD COLUMN IF NOT EXISTS whatsapp_access_token TEXT;

COMMENT ON COLUMN public.tenants.whatsapp_phone_number_id IS 'Meta Phone Number ID (WhatsApp Business API)';
COMMENT ON COLUMN public.tenants.whatsapp_waba_id IS 'WhatsApp Business Account ID (WABA)';
COMMENT ON COLUMN public.tenants.whatsapp_access_token IS 'Kalıcı erişim jetonu (Permanent Token)';
