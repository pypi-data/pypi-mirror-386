"""
TalkLabs Python SDK - Drop-in replacement para ElevenLabs
Uso idêntico ao SDK oficial da ElevenLabs

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
from typing import Optional, Iterator, Dict, Any, List
from dataclasses import dataclass


@dataclass
class VoiceSettings:
    """Configurações de voz (compatível com ElevenLabs)."""
    stability: float = 0.75
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True
    
    def to_dict(self):
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
            "use_speaker_boost": self.use_speaker_boost
        }


class TalkLabsClient:
    """Cliente TalkLabs compatível com ElevenLabs SDK."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:5000"
    ):
        """
        Inicializa cliente TalkLabs.
        
        Args:
            api_key: Chave de API TalkLabs
            base_url: URL base da API (padrão: http://localhost:5000)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    # ============================================================
    # MÉTODO PRINCIPAL: generate()
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
        Gera áudio a partir de texto (método principal).
        
        Exemplo:
            client = TalkLabsClient(api_key="...")
            audio = client.generate(
                text="Olá, mundo!",
                voice="yasmin_alves",
                speed=1.2
            )
            
            with open("output.wav", "wb") as f:
                f.write(audio)
        
        Args:
            text: Texto para sintetizar
            voice: ID da voz (ex: "yasmin_alves")
            model: ID do modelo (padrão: "eleven_multilingual_v2")
            voice_settings: Configurações de voz
            speed: Velocidade de reprodução (0.25-4.0)
            language: Código do idioma (ex: "pt", "en")
        
        Returns:
            bytes: Áudio WAV/MP3
        """
        url = f"{self.base_url}/v1/text-to-speech/{voice}"
        
        payload = {
            "text": text,
            "model_id": model,
            "speed": speed,
            "language_code": language
        }
        
        if voice_settings:
            payload["voice_settings"] = voice_settings.to_dict()
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"TalkLabs API Error: {response.status_code} - {response.text}")
        
        return response.content
    
    # ============================================================
    # MÉTODO: generate_stream() - Streaming HTTP
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
        Gera áudio com streaming (recebe chunks progressivamente).
        
        Exemplo:
            client = TalkLabsClient(api_key="...")
            
            with open("output.wav", "wb") as f:
                for chunk in client.generate_stream(
                    text="Texto longo para streaming...",
                    voice="yasmin_alves"
                ):
                    f.write(chunk)
        
        Args:
            text: Texto para sintetizar
            voice: ID da voz
            model: ID do modelo
            voice_settings: Configurações de voz
            optimize_streaming_latency: Nível de otimização (0-4)
        
        Yields:
            bytes: Chunks de áudio
        """
        url = f"{self.base_url}/v1/text-to-speech/{voice}/stream"
        
        payload = {
            "text": text,
            "model_id": model,
            "optimize_streaming_latency": optimize_streaming_latency
        }
        
        if voice_settings:
            payload["voice_settings"] = voice_settings.to_dict()
        
        with requests.post(url, headers=self.headers, json=payload, stream=True) as response:
            if response.status_code != 200:
                raise Exception(f"TalkLabs API Error: {response.status_code}")
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
    
    # ============================================================
    # MÉTODO: generate_with_timestamps()
    # ============================================================
    
    def generate_with_timestamps(
        self,
        text: str,
        voice: str,
        model: str = "eleven_multilingual_v2",
        speed: float = 1.0
    ) -> Dict[str, Any]:
        """
        Gera áudio com timestamps de palavras.
        
        Exemplo:
            client = TalkLabsClient(api_key="...")
            result = client.generate_with_timestamps(
                text="Olá mundo",
                voice="yasmin_alves"
            )
            
            # Salva áudio
            audio_bytes = base64.b64decode(result["audio_base64"])
            with open("output.wav", "wb") as f:
                f.write(audio_bytes)
            
            # Imprime timestamps
            for word_info in result["alignment"]:
                print(f"{word_info['word']}: {word_info['start']}s - {word_info['end']}s")
        
        Returns:
            dict: {"audio_base64": str, "alignment": [...]}
        """
        url = f"{self.base_url}/v1/text-to-speech/{voice}/with-timestamps"
        
        payload = {
            "text": text,
            "model_id": model,
            "speed": speed
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"TalkLabs API Error: {response.status_code}")
        
        return response.json()
    
    # ============================================================
    # MÉTODO: stream_input() - WebSocket (async)
    # ============================================================
    
    async def stream_input(
        self,
        text_iterator,
        voice: str,
        voice_settings: Optional[VoiceSettings] = None
    ):
        """
        Streaming bidirecional via WebSocket.
        
        Exemplo:
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
                    # Processa chunks de áudio
                    print(f"Recebido {len(audio_chunk)} bytes")
            
            asyncio.run(main())
        """
        ws_url = f"{self.base_url.replace('http', 'ws')}/v1/text-to-speech/{voice}/stream-input"
        
        async with websockets.connect(ws_url) as websocket:
            # Envia autenticação
            auth_msg = {
                "text": " ",
                "xi_api_key": self.api_key
            }
            if voice_settings:
                auth_msg["voice_settings"] = voice_settings.to_dict()
            
            await websocket.send(json.dumps(auth_msg))
            
            # Inicia task de envio de texto
            async def send_text():
                async for text_chunk in text_iterator:
                    await websocket.send(json.dumps({"text": text_chunk}))
                await websocket.send(json.dumps({"flush": True}))
            
            send_task = asyncio.create_task(send_text())
            
            # Recebe áudio
            try:
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if "audio" in data:
                        audio_bytes = base64.b64decode(data["audio"])
                        yield audio_bytes
                    
                    if data.get("isFinal"):
                        break
            finally:
                await send_task
    
    # ============================================================
    # MÉTODO: get_voices() - Lista vozes disponíveis
    # ============================================================
    
    def get_voices(self) -> List[Dict[str, Any]]:
        """
        Lista todas as vozes disponíveis.
        
        Exemplo:
            client = TalkLabsClient(api_key="...")
            voices = client.get_voices()
            
            for voice in voices:
                print(f"{voice['name']} ({voice['voice_id']})")
        
        Returns:
            list: Lista de dicionários com informações de vozes
        """
        url = f"{self.base_url}/v1/voices"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"TalkLabs API Error: {response.status_code}")
        
        return response.json()["voices"]
    
    # ============================================================
    # MÉTODO: get_models() - Lista modelos disponíveis
    # ============================================================
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Lista modelos TTS disponíveis.
        
        Returns:
            list: Lista de modelos
        """
        url = f"{self.base_url}/v1/models"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"TalkLabs API Error: {response.status_code}")
        
        return response.json()["models"]


# ============================================================
# FUNÇÕES DE CONVENIÊNCIA (estilo ElevenLabs)
# ============================================================

def generate(
    text: str,
    voice: str,
    api_key: str,
    model: str = "eleven_multilingual_v2",
    speed: float = 1.0
) -> bytes:
    """
    Função de conveniência para gerar áudio rapidamente.
    
    Exemplo:
        from talklabs import generate
        
        audio = generate(
            text="Olá mundo!",
            voice="yasmin_alves",
            api_key="TALKLABS_SECRET_KEY"
        )
        
        with open("output.wav", "wb") as f:
            f.write(audio)
    """
    client = TalkLabsClient(api_key=api_key)
    return client.generate(text=text, voice=voice, model=model, speed=speed)


def stream(
    text: str,
    voice: str,
    api_key: str,
    model: str = "eleven_multilingual_v2"
) -> Iterator[bytes]:
    """
    Função de conveniência para streaming.
    
    Exemplo:
        from talklabs import stream
        
        with open("output.wav", "wb") as f:
            for chunk in stream(
                text="Texto longo...",
                voice="yasmin_alves",
                api_key="TALKLABS_SECRET_KEY"
            ):
                f.write(chunk)
    """
    client = TalkLabsClient(api_key=api_key)
    return client.generate_stream(text=text, voice=voice, model=model)


# ============================================================
# EXEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    # Exemplo 1: Geração simples
    print("=== Exemplo 1: Geração simples ===")
    client = TalkLabsClient(api_key="TALKLABS_SECRET_KEY")
    
    audio = client.generate(
        text="Olá, eu sou a Yasmin Alves da TalkLabs!",
        voice="yasmin_alves",
        speed=1.2
    )
    
    with open("exemplo1.wav", "wb") as f:
        f.write(audio)
    print("✓ Áudio salvo em exemplo1.wav")
    
    # Exemplo 2: Streaming
    print("\n=== Exemplo 2: Streaming ===")
    with open("exemplo2.wav", "wb") as f:
        for i, chunk in enumerate(client.generate_stream(
            text="Este é um texto mais longo para demonstrar streaming de áudio em tempo real.",
            voice="yasmin_alves"
        )):
            f.write(chunk)
            print(f"✓ Chunk {i+1} recebido ({len(chunk
