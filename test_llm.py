
from llm import get_client
client,model= get_client()

response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],

)
print(response.choices[0].message.content)