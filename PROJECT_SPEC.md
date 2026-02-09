# WhatsApp AI SaaS Platform - Technical Specification

## PROJECT OVERVIEW
Multi-tenant WhatsApp AI chatbot SaaS platform. Each business customer gets modular AI assistant features they can enable/disable.

## TECH STACK
- Python 3.11+ with Flask
- Supabase PostgreSQL (already configured)
- Anthropic Claude API (Sonnet 4, with Vision for images)
- Meta WhatsApp Business API
- Deploy target: Railway

## DATABASE (Already created in Supabase)
**Connection:**
- URL: https://nvqyqhhcsmrjkqcqfeaf.supabase.co
- Service Role Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52cXlxaGhjc21yamtxY3FmZWFmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNzc2NjgwMCwiZXhwIjoyMDUzMzQyODAwfQ.CYcIk8MwDLWD9DgK9vJd9Q_sc92jdvw

**Tables:**
- tenants: id, name, whatsapp_phone_id, modules(jsonb), system_prompt_rules, integrations(jsonb), subscription_plan, subscription_status
- conversations: id, tenant_id, customer_phone, message_type, message_content, image_url, ai_response, module_used, processing_time_ms

**Test tenant already exists:**
- Name: Tuba Muttioğlu Tekstil
- Phone ID: 875250869015662

## MODULES (Enable/Disable per tenant via modules JSONB field)
1. **sales_assistant**: Pre-sale product questions (size, color, availability)
2. **return_exchange**: Defective product handling with image analysis
3. **order_approval**: (Future) Send approval messages 2h after order
4. **cancel_return**: (Future) Cancellation/refund handling
5. **voice_support**: (Future) Voice message transcription
6. **image_support**: Image handling (enabled for return_exchange)

## FEATURES

### 1. WEBHOOK HANDLER
**Endpoint:** `/webhook`

**GET Request (Meta verification):**
- Check hub.mode == "subscribe"
- Check hub.verify_token == "12345"
- Return hub.challenge

**POST Request (Incoming WhatsApp message):**
- Parse Meta webhook payload
- Extract: whatsapp_phone_id, customer_phone, message_type, content
- Handle: text, image
- For audio/video: Send "We don't support voice/video yet, please type your message"

### 2. MESSAGE PROCESSING FLOW
1. Get tenant by whatsapp_phone_id from Supabase
2. Check which modules are enabled in tenant.modules
3. Route to appropriate module handler
4. Get AI response from Claude
5. Send response via WhatsApp
6. Log to conversations table

### 3. SALES ASSISTANT MODULE
**When:** modules.sales_assistant == true
**What:**
- Customer asks about product features, sizes, colors, availability
- Use Claude AI with tenant's system_prompt_rules
- If integrations.butik_sistem.enabled == true: Mock API call (return sample product data)
- Respond with helpful product information

### 4. RETURN/EXCHANGE MODULE
**When:** modules.return_exchange == true AND message_type == "image"
**What:**
- Customer sends defective product image
- Use Claude Vision API to analyze image
- Prompt: "Analyze this product image. Is there visible damage/defect? Describe in detail."
- If defect detected:
  - AI suggests alternative product OR
  - Respond: "Our specialists will contact you shortly" (human handoff)
- Log analysis to conversations

### 5. UNSUPPORTED MEDIA HANDLING
**Audio message:**
```
🎤 We received your voice message!

Voice messages are not supported yet. 
Please type your message instead.

Thank you! 🙏
```

**Video message:** Same pattern

### 6. CLAUDE AI INTEGRATION
**API Key:** (use env `ANTHROPIC_API_KEY` – do not commit real key)

**Text messages:**
```python
anthropic.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=tenant['system_prompt_rules'],
    messages=[{"role": "user", "content": user_message}]
)
```

**Image analysis:**
```python
anthropic.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}},
            {"type": "text", "text": "Analyze this product image for defects..."}
        ]
    }]
)
```

### 7. META WHATSAPP API
**Token:** EAAbngqb3Gx8BQhHgMeUg6EASBhyytWnVDn0hYkq9X7OHZBGEeNPVIFRu3TI5eg9wkJSZBfF85UDfCe2DdUcQpMPjZBJ7PDEFVknh1UggalkZBjVwPAZCEj3ZAlrYlBoVOd7TkWWJR0QTrXSMQ5FarOCHglpFH8hjr8ZA2PiCNoMs5SgCzSriryP0rlZCvG3ciEYWUfS5Mxol4dFdyhFEv9IHHn0grwIUveir44gWaCLoCYNaTZBmDdMrnOleZABSGhIUVacZBj1GIJ1ZCaMVefcTbLdJtviwqCZBYOzAZD

**Send message:**
```
POST https://graph.facebook.com/v21.0/{phone_id}/messages
Headers: Authorization: Bearer {token}
Body: {
  "messaging_product": "whatsapp",
  "to": "{customer_phone}",
  "text": {"body": "{message}"}
}
```

## FILE STRUCTURE
```
/app.py                    - Flask app, webhook handler
/config.py                 - Environment variables
/database.py               - Supabase client, queries
/claude_client.py          - Claude AI wrapper
/whatsapp_client.py        - Meta API wrapper
/modules/
  /sales_assistant.py      - Sales module
  /return_exchange.py      - Return/exchange module
/utils.py                  - Helper functions
/requirements.txt          - Dependencies
/.env.example              - Sample env vars
/README.md                 - Setup instructions
```

## ENVIRONMENT VARIABLES (.env)
```
SUPABASE_URL=https://nvqyqhhcsmrjkqcqfeaf.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52cXlxaGhjc21yamtxY3FmZWFmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNzc2NjgwMCwiZXhwIjoyMDUzMzQyODAwfQ.CYcIk8MwDLWD9DgK9vJd9Q_sc92jdvw
ANTHROPIC_API_KEY=your-anthropic-api-key-here
META_ACCESS_TOKEN=EAAbngqb3Gx8BQhHgMeUg6EASBhyytWnVDn0hYkq9X7OHZBGEeNPVIFRu3TI5eg9wkJSZBfF85UDfCe2DdUcQpMPjZBJ7PDEFVknh1UggalkZBjVwPAZCEj3ZAlrYlBoVOd7TkWWJR0QTrXSMQ5FarOCHglpFH8hjr8ZA2PiCNoMs5SgCzSriryP0rlZCvG3ciEYWUfS5Mxol4dFdyhFEv9IHHn0grwIUveir44gWaCLoCYNaTZBmDdMrnOleZABSGhIUVacZBj1GIJ1ZCaMVefcTbLdJtviwqCZBYOzAZD
META_VERIFY_TOKEN=12345
PORT=5000
```

## ERROR HANDLING
- Log all errors to conversations table (error_message field)
- Graceful error messages to customer
- Retry logic for API calls
- Timeouts: 30s for Claude, 10s for Meta

## LOGGING
- Every conversation to database (conversations table)
- Include: tenant_id, customer_phone, message_type, content, AI response, module_used, processing_time_ms
- Console logs for debugging

## TESTING
- Test with actual WhatsApp messages to 875250869015662
- Test image upload for return/exchange
- Test unsupported media (voice)
- Verify module enable/disable via database

## DEPLOYMENT (Railway)
- Flask runs on PORT from env
- Health check endpoint: GET /health returns {"status": "ok"}
- Auto-deploy from git push

## IMPLEMENTATION NOTES
1. Start with app.py - webhook routes
2. Implement database.py - Supabase connection
3. Build claude_client.py - AI wrapper
4. Add whatsapp_client.py - Meta API
5. Create modules - sales_assistant, return_exchange
6. Add error handling and logging
7. Test locally with ngrok
8. Deploy to Railway

## SUCCESS CRITERIA
- Webhook verifies with Meta (GET request works)
- Receives and processes text messages
- AI responds appropriately based on enabled modules
- Image analysis works for return/exchange
- Logs all conversations to database
- Handles unsupported media gracefully
- Ready for Railway deployment
