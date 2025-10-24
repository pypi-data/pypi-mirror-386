# TalkLabs Python SDK

SDK oficial da **TalkLabs** — compatível com a API ElevenLabs.

Permite gerar áudio realista com vozes personalizadas e streaming em tempo real.

## Instalação
\`\`\`bash
pip install talklabs
\`\`\`

## Exemplo de uso
\`\`\`python
from talklabs import TalkLabsClient

client = TalkLabsClient(
    api_key="YOUR_API_KEY",
    base_url="https://api.talklabs.com.br"
)

audio = client.generate(
    text="Olá do TalkLabs!",
    voice="yasmin_alves"
)

with open("output.wav", "wb") as f:
    f.write(audio)
\`\`\`

## Base URL
- https://api.talklabs.com.br/v1

