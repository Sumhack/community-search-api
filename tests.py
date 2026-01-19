from portkey_ai import Portkey

portkey = Portkey(
  api_key = "17Kpc3zpdJeS9aptj7LBm7Tv1x+x",
#   virtual_key = "openai"
)

response = portkey.chat.completions.create(
  model="@anthropic/claude-sonnet-4-5-20250929",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  max_tokens=100
)

print(response)