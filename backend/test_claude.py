import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-5-haiku-latest",
    max_tokens=200,
    messages=[{"role": "user", "content": "Explain black holes simply"}],
)

print(response.content[0].text)
