"""
TalkLabs Python SDK - Compatível com ElevenLabs
-----------------------------------------------
Versão revisada e expandida para suportar streaming real via WebSocket.

Instalação:
    pip install requests websockets

Uso básico:
    from talklabs import TalkLabsClient
    
    client = TalkLabsClient(api_key="TALKLABS_SECRET_KEY")
    audio = client.generate(text="Olá mundo!", voice="yasmin_alves")
    
    with open("output.wav", "wb") as f:
        f.write(audio)
"""

import requests
import json
import base64
import websockets
import asyncio
import logging
from typing import Optional, Iterator, Dict, Any, List
from dataclasses import dataclass

# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("talklabs")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


# ============================================================
# CLASSE: VoiceSettings
# ============================================================

@dataclass
class VoiceSettings:
    """
    Configurações de voz (compatível com ElevenLabs).
    """
    stability: float = 0.75
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True

    def to_dict(self):
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
            "use_speaker_boost": self.use_speaker_boost,
        }


# ============================================================
# CLASSE PRINCIPAL: TalkLabsClient
# ============================================================

class TalkLabsClient:
    """
    Cliente oficial da TalkLabs compatível com o SDK da ElevenLabs.
    Inclui suporte completo a:
        - Geração síncrona (HTTP)
        - Streaming HTTP (fallback)
        - Streaming bidirecional real (WebSocket)
        - Alinhamento de texto (timestamps)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.talklabs.com.br",
        timeout: int = 90
    ):
        """
        Inicializa cliente TalkLabs.

        Args:
            api_key: Chave de API TalkLabs (ex: "tlk_live_xxxxx")
            base_url: URL base da API
            timeout: Tempo máximo de espera (em segundos)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }

        # URLs derivadas
        self.tts_url = f"{self.base_url}/v1/text-to-speech"
        self.ws_url = self.base_url.replace("https", "wss") + "/stream_input"

        logger.info(f"🔐 TalkLabsClient inicializado com base_url={self.base_url}")
        logger.debug(f"WebSocket endpoint: {self.ws_url}")
    # ============================================================
    # MÉTODO: generate() - Geração síncrona via HTTP
    # ============================================================

    def generate(
        self,
        text: str,
        voice: str,
        model: str = "eleven_multilingual_v2",
        voice_settings: Optional[VoiceSettings] = None,
        speed: float = 1.0,
        language: str = "pt"
    ) -> bytes:
        """
        Gera áudio completo (síncrono) a partir de texto.

        Args:
            text: Texto para sintetizar.
            voice: ID da voz (ex: "yasmin_alves").
            model: Modelo de voz (padrão: "eleven_multilingual_v2").
            voice_settings: Instância opcional de VoiceSettings.
            speed: Velocidade de reprodução (0.25–4.0).
            language: Código do idioma (ex: "pt", "en").

        Returns:
            bytes: Áudio em formato WAV/MP3.
        """
        url = f"{self.tts_url}/{voice}"
        payload = {
            "text": text,
            "model_id": model,
            "speed": speed,
            "language_code": language
        }

        if voice_settings:
            payload["voice_settings"] = voice_settings.to_dict()

        logger.info(f"[TalkLabs] 🗣️  Gerando áudio ({len(text)} chars, voz={voice})")

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error(f"❌ Erro {response.status_code}: {response.text}")
                raise Exception(
                    f"TalkLabs API Error: {response.status_code} - {response.text}"
                )

            logger.info("✅ Áudio gerado com sucesso (modo síncrono).")
            return response.content

        except requests.exceptions.RequestException as e:
            logger.exception("Erro de conexão com TalkLabs API.")
            raise e


    # ============================================================
    # MÉTODO: generate_stream() - Streaming HTTP (Fallback)
    # ============================================================

    def generate_stream(
        self,
        text: str,
        voice: str,
        model: str = "eleven_multilingual_v2",
        voice_settings: Optional[VoiceSettings] = None,
        optimize_streaming_latency: int = 0
    ) -> Iterator[bytes]:
        """
        Gera áudio em chunks usando streaming HTTP.
        ⚠️  Não é streaming em tempo real — apenas incremental.

        Args:
            text: Texto a ser sintetizado.
            voice: ID da voz.
            model: Modelo de voz.
            voice_settings: Configurações de voz.
            optimize_streaming_latency: Nível de otimização (0–4).

        Yields:
            bytes: Chunks de áudio progressivamente.
        """
        url = f"{self.tts_url}/{voice}/stream"
        payload = {
            "text": text,
            "model_id": model,
            "optimize_streaming_latency": optimize_streaming_latency
        }

        if voice_settings:
            payload["voice_settings"] = voice_settings.to_dict()

        logger.info("[TalkLabs] 🌊 Iniciando streaming HTTP (modo fallback).")

        try:
            with requests.post(
                url,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=self.timeout
            ) as response:

                if response.status_code != 200:
                    logger.error(f"❌ Erro {response.status_code} no streaming HTTP.")
                    raise Exception(f"TalkLabs API Error: {response.status_code}")

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

            logger.info("✅ Streaming HTTP finalizado com sucesso.")

        except requests.exceptions.RequestException as e:
            logger.exception("Erro durante streaming HTTP com TalkLabs API.")
            raise e
    # ============================================================
    # MÉTODO: stream_input() - Streaming bidirecional em tempo real
    # ============================================================

    async def stream_input(
        self,
        text_iterator,
        voice: str,
        model: str = "eleven_multilingual_v2",
        speed: float = 1.0,
        language: str = "pt",
        voice_settings: Optional[VoiceSettings] = None,
    ):
        """
        Streaming bidirecional em tempo real usando WebSocket.
        Permite enviar texto incrementalmente e receber chunks de áudio.

        Args:
            text_iterator: iterável assíncrono que fornece partes do texto.
            voice: ID da voz TalkLabs.
            model: Modelo de TTS.
            speed: Velocidade da fala (1.0 = normal).
            language: Código ISO da língua ("pt", "en", etc).
            voice_settings: Configurações opcionais de voz.

        Yields:
            bytes: Chunks de áudio em formato binário (PCM ou WAV).
        """
        ws_url = self.ws_url
        headers = [("Authorization", f"Bearer {self.api_key}")]

        logger.info(f"[TalkLabs] 🎧 Conectando ao WebSocket: {ws_url}")

        try:
            async with websockets.connect(ws_url, extra_headers=headers, ping_interval=20) as ws:
                logger.info("[TalkLabs] ✅ Conexão WebSocket estabelecida.")

                # Envia a mensagem inicial de configuração
                init_payload = {
                    "voice": voice,
                    "model": model,
                    "speed": speed,
                    "language": language,
                }
                if voice_settings:
                    init_payload["voice_settings"] = voice_settings.to_dict()

                await ws.send(json.dumps(init_payload))
                logger.debug(f"[TalkLabs] Enviado init: {json.dumps(init_payload)}")

                # Inicia tarefa de envio do texto
                async def send_text():
                    async for text_chunk in text_iterator:
                        await ws.send(json.dumps({"text": text_chunk}))
                        logger.debug(f"[TalkLabs] 📝 Texto enviado: {text_chunk[:50]!r}")
                    await ws.send(json.dumps({"event": "flush"}))
                    logger.info("[TalkLabs] 🚀 Texto completo enviado.")

                sender = asyncio.create_task(send_text())

                # Recebe áudio progressivamente
                while True:
                    message = await ws.recv()
                    if isinstance(message, bytes):
                        yield message
                        continue

                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        continue

                    # Fim do stream
                    if data.get("event") == "end_of_stream":
                        logger.info("[TalkLabs] 🏁 Fim do streaming.")
                        break

                    # Logs de eventos de status
                    if data.get("event") == "error":
                        logger.error(f"[TalkLabs] ❌ Erro no stream: {data}")
                        break

                await sender

        except Exception as e:
            logger.exception("[TalkLabs] Erro durante comunicação WebSocket.")
            raise e

    # ============================================================
    # MÉTODO: generate_with_timestamps()
    # ============================================================

    def generate_with_timestamps(
        self,
        text: str,
        voice: str,
        model: str = "eleven_multilingual_v2",
        speed: float = 1.0,
        language: str = "pt",
    ) -> Dict[str, Any]:
        """
        Gera áudio com timestamps de palavras (quando disponível).

        Returns:
            dict: {"audio_base64": str, "alignment": [{"word": ..., "start": ..., "end": ...}]}
        """
        url = f"{self.tts_url}/{voice}/with-timestamps"
        payload = {
            "text": text,
            "model_id": model,
            "speed": speed,
            "language_code": language,
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            if response.status_code != 200:
                logger.error(f"❌ Erro {response.status_code}: {response.text}")
                raise Exception(f"TalkLabs API Error: {response.status_code}")

            data = response.json()
            logger.info("✅ Geração com timestamps concluída.")
            return data
        except requests.exceptions.RequestException as e:
            logger.exception("Erro ao gerar timestamps de áudio.")
            raise e


    # ============================================================
    # MÉTODO: get_voices()
    # ============================================================

    def get_voices(self) -> List[Dict[str, Any]]:
        """
        Retorna a lista de vozes disponíveis na API TalkLabs.
        """
        url = f"{self.base_url}/v1/voices"

        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                raise Exception(f"TalkLabs API Error: {response.status_code}")
            voices = response.json().get("voices", [])
            logger.info(f"🎙️  {len(voices)} vozes disponíveis.")
            return voices
        except Exception as e:
            logger.exception("Erro ao listar vozes disponíveis.")
            raise e


    # ============================================================
    # MÉTODO: get_models()
    # ============================================================

    def get_models(self) -> List[Dict[str, Any]]:
        """
        Retorna os modelos de TTS disponíveis.
        """
        url = f"{self.base_url}/v1/models"
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                raise Exception(f"TalkLabs API Error: {response.status_code}")
            models = response.json().get("models", [])
            logger.info(f"🧠 {len(models)} modelos disponíveis.")
            return models
        except Exception as e:
            logger.exception("Erro ao listar modelos disponíveis.")
            raise e
# ============================================================
# FUNÇÕES DE CONVENIÊNCIA (modo simples)
# ============================================================

def generate(
    text: str,
    voice: str,
    api_key: str,
    base_url: str = "https://api.talklabs.com.br",
    model: str = "eleven_multilingual_v2",
    speed: float = 1.0,
) -> bytes:
    """
    Função simples de geração TTS.
    """
    client = TalkLabsClient(api_key=api_key, base_url=base_url)
    return client.generate(text=text, voice=voice, model=model, speed=speed)


def stream(
    text: str,
    voice: str,
    api_key: str,
    base_url: str = "https://api.talklabs.com.br",
    model: str = "eleven_multilingual_v2",
) -> Iterator[bytes]:
    """
    Função simples de streaming TTS.
    """
    client = TalkLabsClient(api_key=api_key, base_url=base_url)
    return client.generate_stream(text=text, voice=voice, model=model)
# ============================================================
# EXEMPLOS DE USO (para testes via terminal)
# ============================================================

if __name__ == "__main__":
    import os

    API_KEY = os.getenv("TALKLABS_API_KEY", "tlk_live_CAqeEKqKxea1zMcdaucWgE6Qem9Jem1")

    print("=== 🔊 Teste TalkLabs SDK ===")
    client = TalkLabsClient(api_key=API_KEY)

    # Exemplo 1 — Geração simples
    print("\n🎤 Testando geração simples...")
    audio = client.generate(
        text="Olá! Eu sou a Yasmin da TalkLabs. Bem-vindo ao novo SDK!",
        voice="yasmin_alves",
        speed=1.1,
    )
    with open("teste_sync.wav", "wb") as f:
        f.write(audio)
    print("✅ Áudio salvo em teste_sync.wav")

    # Exemplo 2 — Streaming HTTP
    print("\n🌊 Testando streaming HTTP (modo fallback)...")
    with open("teste_stream.wav", "wb") as f:
        for i, chunk in enumerate(
            client.generate_stream(
                text="Este é um teste de streaming incremental. A voz da Yasmin deve aparecer suave e natural.",
                voice="yasmin_alves",
            )
        ):
            f.write(chunk)
            print(f"Chunk {i+1} recebido ({len(chunk)} bytes)")

    # Exemplo 3 — Listagem
    print("\n🎙️  Listando vozes disponíveis...")
    for v in client.get_voices():
        print(f"- {v.get('voice_id')} → {v.get('name')}")

    print("\n🧠 Listando modelos disponíveis...")
    for m in client.get_models():
        print(f"- {m.get('model_id')} ({m.get('description', 'sem descrição')})")

    print("\n✅ Teste finalizado com sucesso!")
