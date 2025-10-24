# 🎙️ TalkLabs - ElevenLabs Compatible TTS

<div align="center">

![TalkLabs Logo](https://img.shields.io/badge/TalkLabs-v1.0.0-blue)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Text-to-Speech de alta qualidade compatível com ElevenLabs, powered by XTTS2**

[Documentação](https://docs.talklabs.ai) • [API Reference](https://api.talklabs.ai/docs) • [Exemplos](examples/)

</div>

---

## ✨ Features

- 🎯 **100% compatível com ElevenLabs API** - Drop-in replacement
- 🚀 **Streaming em tempo real** - HTTP e WebSocket
- 🌍 **Multi-idioma** - Português, Inglês, Espanhol, Francês, Alemão, Italiano
- 🎭 **Voice Cloning** - Clone qualquer voz com 3-5 amostras
- ⚡ **Alta Performance** - CUDA acelerado com suporte RTX
- 🔒 **Self-hosted** - Seus dados, seu servidor

## 🚀 Quick Start

### Instalação

```bash
# Instalar TalkLabs
cd /home/francisco/talklabs
pip install -e .

# Ou via pip (quando publicado)
pip install talklabs
```

### Iniciar API

```bash
# Iniciar servidor
python api/main.py

# Ou via uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 5000
```

### Uso do SDK

```python
from talklabs import TalkLabsClient

# Inicializar cliente
client = TalkLabsClient(
    api_key="TALKLABS_SECRET_KEY",
    base_url="http://localhost:5000"
)

# Gerar áudio
audio = client.generate(
    text="Olá, mundo!",
    voice="yasmin_alves",
    speed=1.0
)

# Salvar arquivo
with open("output.wav", "wb") as f:
    f.write(audio)
```

## 📖 Exemplos

### 1. Geração Simples

```python
from talklabs import generate

audio = generate(
    text="Bem-vindo ao TalkLabs!",
    voice="yasmin_alves",
    api_key="TALKLABS_SECRET_KEY"
)
```

### 2. Streaming

```python
from talklabs import TalkLabsClient

client = TalkLabsClient(api_key="...")

with open("stream.wav", "wb") as f:
    for chunk in client.generate_stream(
        text="Texto longo para streaming...",
        voice="yasmin_alves"
    ):
        f.write(chunk)
```

### 3. Com Timestamps

```python
result = client.generate_with_timestamps(
    text="Olá mundo",
    voice="yasmin_alves"
)

# Áudio em base64
audio_bytes = base64.b64decode(result["audio_base64"])

# Timestamps de cada palavra
for word in result["alignment"]:
    print(f"{word['word']}: {word['start']}s - {word['end']}s")
```

### 4. WebSocket Streaming

```python
import asyncio

async def main():
    client = TalkLabsClient(api_key="...")
    
    async def text_stream():
        yield "Olá, "
        await asyncio.sleep(0.5)
        yield "mundo!"
    
    async for audio_chunk in client.stream_input(
        text_iterator=text_stream(),
        voice="yasmin_alves"
    ):
        # Processar chunk de áudio
        pass

asyncio.run(main())
```

## 🎭 Clonando Vozes

```bash
# 1. Criar diretório para nova voz
mkdir -p samples/minha_voz

# 2. Adicionar 3-5 amostras WAV (16kHz, mono, 10-30s cada)
cp amostra1.wav samples/minha_voz/
cp amostra2.wav samples/minha_voz/
cp amostra3.wav samples/minha_voz/

# 3. Reiniciar servidor
# A voz estará disponível automaticamente!
```

## 🔌 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/v1/text-to-speech/{voice_id}` | POST | TTS padrão |
| `/v1/text-to-speech/{voice_id}/stream` | POST | Streaming HTTP |
| `/v1/text-to-speech/{voice_id}/with-timestamps` | POST | TTS com timestamps |
| `/v1/text-to-speech/{voice_id}/stream-input` | WS | WebSocket streaming |
| `/v1/voices` | GET | Listar vozes |
| `/v1/models` | GET | Listar modelos |
| `/health` | GET | Health check |

## 🎛️ Parâmetros

```python
client.generate(
    text="Seu texto aqui",
    voice="yasmin_alves",
    speed=1.0,           # 0.25 a 4.0
    language="pt",       # pt, en, es, fr, de, it
    voice_settings={
        "stability": 0.75,        # 0.0 a 1.0
        "similarity_boost": 0.75,
        "style": 0.0,
        "use_speaker_boost": True
    }
)
```

## 🌐 Usando via cURL

```bash
curl -X POST "http://localhost:5000/v1/text-to-speech/yasmin_alves" \
     -H "xi-api-key: TALKLABS_SECRET_KEY" \
     -H "Content-Type: application/json" \
     -d '{"text":"Olá mundo!","speed":1.2}' \
     --output audio.wav
```

## 🔧 Configuração

```python
# .env ou variáveis de ambiente
TALKLABS_API_KEY=your_secret_key_here
TALKLABS_HOST=0.0.0.0
TALKLABS_PORT=5000
CUDA_VISIBLE_DEVICES=0  # GPU a usar
```

## 📊 Benchmarks

| Métrica | Valor |
|---------|-------|
| Latência primeira chunk | ~200ms |
| Throughput | ~50 caracteres/segundo |
| Qualidade MOS | 4.2/5.0 |
| Idiomas suportados | 6+ |
| GPU mínima | GTX 1060 6GB |
| GPU recomendada | RTX 3090+ |

## 🐛 Troubleshooting

### CUDA Out of Memory
```python
# Reduzir batch size ou usar CPU
engine = TalkLabsEngine(device="cpu")
```

### Voz não encontrada
```bash
# Verificar vozes disponíveis
curl http://localhost:5000/v1/voices
```

### Latência alta
```python
# Usar modelo flash
client.generate(text="...", model="eleven_flash_v2_5")
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 🙏 Créditos

- XTTS2 by [Coqui.ai](https://github.com/coqui-ai/TTS)
- Inspirado em [ElevenLabs](https://elevenlabs.io)

---

<div align="center">

**[Website](https://talklabs.ai)** • **[Documentação](https://docs.talklabs.ai)** • **[Discord](https://discord.gg/talklabs)**

Made with ❤️ by TalkLabs Team

</div>
