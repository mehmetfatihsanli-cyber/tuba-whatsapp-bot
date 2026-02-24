# n8n MCP – Notlar (sonra bakılacak)

- **Instance:** https://herzamanki.app.n8n.cloud
- **MCP:** @makafeli/n8n-workflow-builder, `.cursor/mcp.json` içinde N8N_HOST + N8N_API_KEY ile tanımlı. Cursor’da “n8n” 23 tool ile açılıyor (bağlantı tamam).
- **Sorun:** `list_workflows` / `get_workflow` çağrıldığında yanıt workflow listesi (JSON) değil, n8n arayüz sayfasının HTML’i geliyor. Paket muhtemelen n8n Cloud API’ye değil arayüz adresine istek atıyor veya API key header’ı (X-N8N-API-KEY) doğru gitmiyor.
- **Denenen:** N8N_HOST’a `/api/v1` eklenince MCP “Disabled” oldu; geri alındı.
- **İleride:** İstenirse projede (Flask) n8n REST API’yi doğrudan çağıran endpoint eklenebilir: GET .../api/v1/workflows, X-N8N-API-KEY ile; panelde workflow listesi/gösterimi böyle yapılabilir.

Son güncelleme: Şubat 2026
