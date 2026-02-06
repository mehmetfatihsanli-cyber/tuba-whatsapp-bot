import anthropic

client = anthropic.Anthropic(api_key="REDACTED")

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Merhaba! Sadece 'Test başarılı!' yaz."}
    ]
)

print(message.content[0].text)
