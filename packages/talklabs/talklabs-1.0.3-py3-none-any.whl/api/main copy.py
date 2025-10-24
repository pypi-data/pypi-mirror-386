"""
TalkLabs API - Compatível com ElevenLabs SDK
Endpoints implementados:
- POST /v1/text-to-speech/{voice_id}
- POST /v1/text-to-speech/{voice_id}/stream
- POST /v1/text-to-speech/{voice_id}/with-timestamps
- WS /v1/text-to-speech/{voice_id}/stream-input
- GET /v1/voices
- GET /v1/models
"""
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
import asyncio
import sys
import os
import io
import time
import logging
from logging.handlers import RotatingFileHandler
from fastapi import UploadFile, File
import shutil
import librosa
import soundfile as sf
import uuid
from datetime import datetime, timedelta
from usage_tracker import usage_tracker
from usage_reports import report_generator
from core.xtts_engine import TalkLabsEngine
from fastapi import Request
from dotenv import load_dotenv
from supabase import create_client
import os
from fastapi.responses import JSONResponse
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY não foram encontradas no ambiente")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


engine = TalkLabsEngine()




async def verify_api_key(xi_api_key: str = Header(None)) -> dict:
    """
    🔑 Valida a API key no Supabase em vez de usar dicionário hardcoded.
    Retorna os dados do cliente se a chave for válida e ativa.
    """

    if not xi_api_key:
        raise HTTPException(status_code=401, detail="Missing xi-api-key header")

    response = supabase.table("talklabs_clients") \
        .select("id, client_name, email, is_active, pricing_plan_id, environment") \
        .eq("api_key_public", xi_api_key) \
        .eq("environment", "production") \
        .single() \
        .execute()

    client = response.data
    if not client:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not client.get("is_active"):
        raise HTTPException(status_code=403, detail="Account inactive or suspended")

    # ✅ Corrigido: grava data real de acesso
    from datetime import datetime
    supabase.table("talklabs_clients") \
        .update({"last_activity_at": datetime.utcnow().isoformat()}) \
        .eq("id", client["id"]) \
        .execute()

    logging.info(f"[AUTH] {client['client_name']} ({client['id']}) autenticado com sucesso.")

    return client



# ============================================================
# 2. ADICIONE ESTA FUNÇÃO (pode ser depois das importações)
# ============================================================


def calculate_audio_duration(audio_bytes: bytes) -> float:
    """Calcula a duração de um áudio (rápido e seguro)"""
    import soundfile as sf
    import io

    try:
        with sf.SoundFile(io.BytesIO(audio_bytes)) as f:
            frames = f.frames
            sr = f.samplerate
            duration = frames / sr
        return round(duration, 2)
    except Exception:
        # Fallback aproximado (se arquivo estiver corrompido)
        return round(len(audio_bytes) / (24000 * 2), 2)  # assume 24kHz, 16-bit
        

app = FastAPI(
    title="TalkLabs API",
    description="ElevenLabs-compatible TTS API powered by XTTS2",
    version="1.0.0"
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    🛑 Captura qualquer exceção não tratada e registra no log.
    """
    error_trace = traceback.format_exc()
    logging.error(f"[UNHANDLED ERROR] {request.url.path}\n{error_trace}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno inesperado. A equipe da TalkLabs foi notificada.",
            "path": str(request.url.path),
        },
    )


@app.middleware("http")
async def enforce_api_key(request: Request, call_next):
    """
    Middleware global para validar chaves via Supabase.
    Garante que todas as rotas /v1/* só sejam acessíveis por clientes ativos.
    """
    path = request.url.path

    # Permite rotas públicas (docs, health, dashboard)
    if not path.startswith("/v1/"):
        return await call_next(request)

    xi_api_key = request.headers.get("xi-api-key")
    if not xi_api_key:
        return Response(
            content=json.dumps({"detail": "Missing xi-api-key header"}),
            status_code=401,
            media_type="application/json"
        )

    try:
        await verify_api_key(xi_api_key)
    except HTTPException as e:
        return Response(
            content=json.dumps({"detail": e.detail}),
            status_code=e.status_code,
            media_type="application/json"
        )
    except Exception as e:
        return Response(
            content=json.dumps({"detail": str(e)}),
            status_code=500,
            media_type="application/json"
        )

    return await call_next(request)



# Caminho do log de acessos
LOG_FILE = "/home/francisco/talklabs/logs/api_access.log"



# ============================================================
# MODELOS DE DADOS (ElevenLabs-compatible)
# ============================================================

class VoiceSettings(BaseModel):
    stability: Optional[float] = Field(default=0.75, ge=0.0, le=1.0)
    similarity_boost: Optional[float] = Field(default=0.75, ge=0.0, le=1.0)
    style: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    use_speaker_boost: Optional[bool] = True


class TTSRequest(BaseModel):
    text: str
    model_id: Optional[str] = "eleven_multilingual_v2"
    voice_settings: Optional[VoiceSettings] = None
    language_code: Optional[str] = "pt"
    speed: Optional[float] = Field(default=1.0, ge=0.25, le=4.0)
    
    # Parâmetros avançados
    previous_text: Optional[str] = None
    next_text: Optional[str] = None
    previous_request_ids: Optional[List[str]] = None
    pronunciation_dictionary_locators: Optional[List[Dict]] = None
    apply_text_normalization: Optional[str] = "auto"


class StreamRequest(BaseModel):
    text: str
    model_id: Optional[str] = "eleven_multilingual_v2"
    voice_settings: Optional[VoiceSettings] = None
    optimize_streaming_latency: Optional[int] = Field(default=0, ge=0, le=4)


class Voice(BaseModel):
    voice_id: str
    name: str
    category: str = "premade"
    description: str = ""
    labels: Dict[str, str] = {}
    samples: Optional[List[Dict]] = None


class Model(BaseModel):
    model_id: str
    name: str
    can_do_text_to_speech: bool = True
    can_do_voice_conversion: bool = False
    languages: List[Dict[str, str]]
    description: str

# ============================================================
# 4. SUBSTITUA O ENDPOINT stream POR ESTE:
# ============================================================

@app.post("/v1/text-to-speech/{voice_id:path}/stream")
async def text_to_speech_stream(
    voice_id: str,
    request: StreamRequest,
    xi_api_key: str = Header(None)
):
    """TTS com streaming de áudio + rastreamento"""
    client = await verify_api_key(xi_api_key)

    
    total_audio_duration = 0.0
    all_audio = []
    
    async def generate_audio_chunks():
        nonlocal total_audio_duration
        
        try:
            sentences = request.text.replace("!", ".").replace("?", ".").split(".")
            sentences = [s.strip() for s in sentences if s.strip()]
            
            for sentence in sentences:
                audio = engine.synthesize(
                    text=sentence,
                    speaker=voice_id,
                    temperature=request.voice_settings.stability if request.voice_settings else 0.75
                )
                
                all_audio.append(audio)
                total_audio_duration += calculate_audio_duration(audio)
                yield audio
                await asyncio.sleep(0.01)
                
        except Exception as e:
            print(f"[Stream Error] {e}")
    
    # Gera o streaming
    response = StreamingResponse(
        generate_audio_chunks(),
        media_type="audio/wav",
        headers={"Content-Disposition": f'attachment; filename="{voice_id}_stream.wav"'}
    )
    
    # 📊 REGISTRA O USO
    usage_tracker.log_usage(
        api_key=xi_api_key,
        client_name=client["client_name"],
        endpoint="/v1/text-to-speech/stream",
        voice_id=voice_id,
        text=request.text,
        audio_duration=total_audio_duration,
        model_id=request.model_id or "eleven_multilingual_v2"
    )
    
    return response
    

# ============================================================
# 3. SUBSTITUA O ENDPOINT text_to_speech POR ESTE:
# ============================================================

@app.post("/v1/text-to-speech/{voice_id:path}")
async def text_to_speech(
    voice_id: str,
    request: TTSRequest,
    xi_api_key: str = Header(None),
    enable_logging: bool = True
):
    """Converte texto em fala com rastreamento de uso"""
    client = await verify_api_key(xi_api_key)

    
    try:
        temperature = 0.75
        if request.voice_settings:
            temperature = request.voice_settings.stability
        
        # 🔧 Normaliza o identificador da voz (garante formato "pt-br/xxxx")
        voice_id = (voice_id or "").strip()
        if not voice_id.startswith("pt-br/"):
            voice_id = f"pt-br/{voice_id}"

        audio = engine.synthesize(
            text=request.text,
            speaker=voice_id,
            language=request.language_code or "pt",
            speed=request.speed,
            temperature=temperature
        )

        
        # 📊 REGISTRA O USO
        audio_duration = calculate_audio_duration(audio)
        usage_tracker.log_usage(
            api_key=xi_api_key,
            client_name=client["client_name"],
            endpoint="/v1/text-to-speech",
            voice_id=voice_id,
            text=request.text,
            audio_duration=audio_duration,
            model_id=request.model_id or "eleven_multilingual_v2",
            language_code=request.language_code or "pt",
            metadata={
                "speed": request.speed,
                "temperature": temperature
            }
        )
        
        return Response(
            content=audio,
            media_type="audio/wav",
            headers={
                "Content-Type": "audio/mpeg",
                "Content-Disposition": f'attachment; filename="{voice_id}.wav"',
                "X-Audio-Duration": str(audio_duration),
                "X-Text-Characters": str(len(request.text))
            }
        )
    except Exception:
        logging.exception("[TTS ERROR]")
        raise HTTPException(status_code=500, detail="Erro interno durante a síntese de voz.")




# ============================================================
# ENDPOINT 3: TTS com timestamps
# ============================================================


# ============================================================
# 5. SUBSTITUA O ENDPOINT with-timestamps POR ESTE:
# ============================================================

@app.post("/v1/text-to-speech/{voice_id:path}/with-timestamps")
async def text_to_speech_with_timestamps(
    voice_id: str,
    request: TTSRequest,
    xi_api_key: str = Header(None)
):
    """TTS com timestamps + rastreamento"""
    client = await verify_api_key(xi_api_key)

    
    try:
        import base64
        
        audio = engine.synthesize(
            text=request.text,
            speaker=voice_id,
            speed=request.speed
        )
        
        audio_duration = calculate_audio_duration(audio)
        
        words = request.text.split()
        duration_per_char = 0.08
        
        alignment = []
        current_time = 0.0
        
        for word in words:
            char_count = len(word)
            duration = char_count * duration_per_char
            
            alignment.append({
                "word": word,
                "start": round(current_time, 3),
                "end": round(current_time + duration, 3)
            })
            current_time += duration + 0.1
        
        # 📊 REGISTRA O USO
        usage_tracker.log_usage(
            api_key=xi_api_key,
            client_name=client["client_name"],
            endpoint="/v1/text-to-speech/with-timestamps",
            voice_id=voice_id,
            text=request.text,
            audio_duration=audio_duration,
            model_id=request.model_id or "eleven_multilingual_v2",
            language_code=request.language_code or "pt"
        )
        
        return {
            "audio_base64": base64.b64encode(audio).decode('utf-8'),
            "alignment": alignment,
            "normalized_alignment": alignment,
            "audio_duration_seconds": audio_duration,
            "characters_processed": len(request.text)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================
# ENDPOINT 4: WebSocket streaming (input streaming)
# ============================================================

@app.websocket("/v1/text-to-speech/{voice_id:path}/stream-input")
async def websocket_stream_input(websocket: WebSocket, voice_id: str):
    await websocket.accept()

    try:
        # 1️⃣ Recebe autenticação
        auth_msg = await websocket.receive_text()
        auth_data = json.loads(auth_msg)
        api_key = auth_data.get("xi_api_key")
        if not api_key:
            await websocket.send_json({"error": "Missing xi_api_key"})
            await websocket.close()
            return

        # 2️⃣ Validação real via Supabase
        try:
            client = await verify_api_key(api_key)
        except HTTPException as e:
            await websocket.send_json({"error": e.detail})
            await websocket.close()
            return
        except Exception as e:
            await websocket.send_json({"error": str(e)})
            await websocket.close()
            return

        logging.info(f"[WS ACCESS] {client['client_name']} | {api_key} | {time.strftime('%Y-%m-%d %H:%M:%S')}")

        buffer = ""

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if "text" in message:
                buffer += message["text"]

                if any(p in buffer for p in [".", "!", "?"]):
                    audio = await asyncio.to_thread(
                        engine.synthesize,
                        text=buffer,
                        speaker=voice_id,
                        temperature=message.get("voice_settings", {}).get("stability", 0.75)
                    )

                    import base64
                    audio_b64 = base64.b64encode(audio).decode("utf-8")

                    await websocket.send_json({
                        "audio": audio_b64,
                        "isFinal": False,
                        "normalizedAlignment": []
                    })
                    buffer = ""

            elif message.get("flush"):
                if buffer:
                    audio = await asyncio.to_thread(engine.synthesize, text=buffer, speaker=voice_id)
                    import base64
                    await websocket.send_json({
                        "audio": base64.b64encode(audio).decode("utf-8"),
                        "isFinal": True
                    })
                break

    except WebSocketDisconnect:
        print(f"[WebSocket] Cliente desconectado: {voice_id}")
    except Exception as e:
        print(f"[WebSocket Error] {e}")
        await websocket.close()



# ============================================================
# ENDPOINT 5: Listar vozes disponíveis
# ============================================================

@app.get("/v1/voices")
async def get_voices():
    """
    Lista todas as vozes disponíveis (compatível com ElevenLabs).
    
    Exemplo:
    curl "http://localhost:5000/v1/voices" \\
         -H "xi-api-key: TALKLABS_SECRET_KEY"
    """
    voices = []
    for voice_id, samples in engine.speakers.items():
        voices.append({
            "voice_id": voice_id,
            "name": voice_id.replace("_", " ").title(),
            "category": "cloned",
            "description": f"Voz clonada com {len(samples)} amostras",
            "labels": {
                "accent": "brazilian",
                "age": "young",
                "gender": "female" if "fem" in voice_id or "yasmin" in voice_id else "male"
            },
            "samples": [{"file_name": s.split("/")[-1]} for s in samples[:3]]
        })
    
    return {"voices": voices}


# ============================================================
# ENDPOINT 6: Listar modelos disponíveis
# ============================================================

@app.get("/v1/models")
async def get_models():
    """
    Lista modelos TTS disponíveis (compatível com ElevenLabs).
    """
    return {
        "models": [
            {
                "model_id": "eleven_multilingual_v2",
                "name": "XTTS v2 Multilingual",
                "can_do_text_to_speech": True,
                "can_do_voice_conversion": False,
                "languages": [
                    {"language_id": "pt", "name": "Portuguese"},
                    {"language_id": "en", "name": "English"},
                    {"language_id": "es", "name": "Spanish"},
                    {"language_id": "fr", "name": "French"},
                    {"language_id": "de", "name": "German"},
                    {"language_id": "it", "name": "Italian"},
                ],
                "description": "Modelo multilíngue de alta qualidade baseado em XTTS2"
            },
            {
                "model_id": "eleven_flash_v2_5",
                "name": "XTTS Flash (Low Latency)",
                "can_do_text_to_speech": True,
                "can_do_voice_conversion": False,
                "languages": [{"language_id": "pt", "name": "Portuguese"}],
                "description": "Versão otimizada para baixa latência"
            }
        ]
    }


# ============================================================
# ENDPOINT 7: Health check
# ============================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "voices_loaded": len(engine.speakers),
        "device": engine.device
    }


# ============================================================
# DOCUMENTAÇÃO INTERATIVA
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "TalkLabs API - ElevenLabs Compatible",
        "docs": "/docs",
        "endpoints": {
            "text_to_speech": "POST /v1/text-to-speech/{voice_id}",
            "streaming": "POST /v1/text-to-speech/{voice_id}/stream",
            "timestamps": "POST /v1/text-to-speech/{voice_id}/with-timestamps",
            "websocket": "WS /v1/text-to-speech/{voice_id}/stream-input",
            "voices": "GET /v1/voices",
            "models": "GET /v1/models"
        }
    }

CLONE_TEMP_DIR = "/home/francisco/talklabs/clone_publico_temp"
os.makedirs(CLONE_TEMP_DIR, exist_ok=True)


@app.post("/v1/clone-de-voz")
async def clone_de_voz(
    xi_api_key: str = Header(None),
    file: UploadFile = File(...),
):
    client = await verify_api_key(xi_api_key)

    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado não é um áudio válido.")

    CLONE_TEMP_DIR = "/home/francisco/talklabs/clone_publico_temp"
    os.makedirs(CLONE_TEMP_DIR, exist_ok=True)

    timestamp = int(time.time())
    filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    temp_path = os.path.join(CLONE_TEMP_DIR, filename)

    # 💾 Salva o arquivo recebido
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        voice_uuid = str(uuid.uuid4())[:8]
        voice_id = f"pt-br/publico_{voice_uuid}"
        voice_dir = f"/home/francisco/talklabs/samples/{voice_id}"
        os.makedirs(voice_dir, exist_ok=True)

        final_path = os.path.join(voice_dir, "sample.wav")

        # ✅ Processamento assíncrono
        wav, sr = await asyncio.to_thread(librosa.load, temp_path, sr=24000, mono=True)
        await asyncio.to_thread(sf.write, final_path, wav, sr)

        # 🔊 Registra no mecanismo
        engine.speakers[voice_id] = [final_path]
        logging.info(f"[CLONE] Nova voz registrada: {voice_id}")

        os.remove(temp_path)

        return {
            "status": "success",
            "voice_id": voice_id,
            "samples": [final_path],
            "message": "Voz clonada com sucesso e pronta para uso."
        }

    except Exception as e:
        logging.error(f"[CLONE ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar o áudio: {e}")



@app.post("/v1/clone-de-voz/privado")
async def clone_de_voz_privado(
    xi_api_key: str = Header(None),
    file: UploadFile = File(...),
):
    """
    📥 Clona voz autenticada e vincula ao cliente.
    As vozes geradas são tratadas como 'premium' (nível das vozes padrão).
    """
    client = await verify_api_key(xi_api_key)

    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado não é um áudio válido.")

    try:
        # 🎯 Estrutura de diretório do cliente
        base_dir = f"/home/francisco/talklabs/samples/pt-br/user_{client['id']}"
        os.makedirs(base_dir, exist_ok=True)

        # 🧠 Gera IDs
        voice_uuid = str(uuid.uuid4())[:8]
        voice_id = f"pt-br/user_{client['id']}_{voice_uuid}"
        clone_dir = os.path.join(base_dir, f"clone_{voice_uuid}")
        os.makedirs(clone_dir, exist_ok=True)

        # 💾 Salva e normaliza
        temp_path = os.path.join(clone_dir, file.filename)
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        wav, sr = librosa.load(temp_path, sr=24000, mono=True)
        final_path = os.path.join(clone_dir, "sample.wav")
        sf.write(final_path, wav, sr)

        # 🔊 Registra no mecanismo TTS
        engine.speakers[voice_id] = [final_path]

        # 🧾 Salva no Supabase
        supabase.table("talklabs_clones").insert({
            "client_id": client["id"],
            "voice_id": voice_id,
            "file_path": final_path,
            "created_at": datetime.utcnow().isoformat(),
            "synced_with_lovable": False
        }).execute()

        # 💞 (Opcional) Sincroniza com Lovable
        lovable_sync = False
        try:
            import requests
            res = requests.post("https://api.lovable.so/voices/sync", json={
                "voice_id": voice_id,
                "client_id": client["id"],
                "email": client["email"],
                "file_path": final_path
            }, timeout=3)
            if res.status_code == 200:
                lovable_sync = True
        except Exception:
            logging.exception("[LOVABLE SYNC] Erro inesperado ao sincronizar com Lovable:")


        # ✅ Resposta padronizada enterprise
        return {
            "status": "success",
            "message": "Voz clonada com sucesso e associada ao seu perfil.",
            "data": {
                "voice_id": voice_id,
                "path": final_path,
                "lovable_sync": lovable_sync,
                "client_id": client["id"],
                "email": client["email"]
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        }

    except Exception as e:
        logging.error(f"[PRIVATE CLONE ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar o áudio: {e}")


# ============================================================
# 6. ADICIONE ESTES NOVOS ENDPOINTS NO FINAL DO ARQUIVO
# ============================================================

@app.get("/v1/usage")
async def get_my_usage(xi_api_key: str = Header(None)):
    """Retorna o uso total da sua API key"""
    client = await verify_api_key(xi_api_key)

    return usage_tracker.get_usage_by_key(xi_api_key)


@app.get("/v1/usage/history")
async def get_usage_history(
    xi_api_key: str = Header(None),
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Retorna histórico detalhado de uso"""
    client = await verify_api_key(xi_api_key)

    return {
        "history": usage_tracker.get_usage_history(
            xi_api_key, 
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
    }


@app.get("/v1/usage/stats")
async def get_usage_stats(
    xi_api_key: str = Header(None),
    period: str = "day"
):
    """Retorna estatísticas agrupadas por período"""
    client = await verify_api_key(xi_api_key)

    
    if period not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=400, 
            detail="period deve ser 'day', 'week' ou 'month'"
        )
    
    return {
        "period": period,
        "stats": usage_tracker.get_usage_stats_by_period(xi_api_key, period)
    }


@app.get("/v1/admin/usage/all")
async def get_all_usage(admin_key: str = Header(None)):
    """Retorna uso de todos os clientes (apenas admin)"""
    ADMIN_KEY = "admin_tlk_secure_2025"
    
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    clients = usage_tracker.get_all_clients_usage()
    
    total_requests = sum(c["total_requests"] for c in clients)
    total_characters = sum(c["total_characters"] for c in clients)
    total_tokens = sum(c["total_tokens"] for c in clients)
    total_audio_seconds = sum(c["total_audio_seconds"] for c in clients)
    
    return {
        "total_clients": len(clients),
        "overall_stats": {
            "total_requests": total_requests,
            "total_characters": total_characters,
            "total_tokens": total_tokens,
            "total_audio_seconds": round(total_audio_seconds, 2),
            "total_audio_hours": round(total_audio_seconds / 3600, 2)
        },
        "clients": clients
    }


@app.get("/v1/reports/monthly")
async def get_monthly_report(
    xi_api_key: str = Header(None),
    year: Optional[int] = None,
    month: Optional[int] = None,
    format: str = "json"
):
    """Gera relatório mensal"""
    client = await verify_api_key(xi_api_key)

    
    report = report_generator.generate_monthly_report(
        api_key=xi_api_key,
        year=year,
        month=month
    )
    
    if format == "csv":
        from fastapi.responses import StreamingResponse
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Período", "API Key", "Cliente", "Requisições", "Caracteres",
            "Tokens", "Áudio (segundos)", "Áudio (minutos)", "Vozes Únicas"
        ])
        
        for client in report.get("clients", []):
            writer.writerow([
                report["period"],
                client["api_key"],
                client["client_name"],
                client["total_requests"],
                client["total_characters"],
                client["total_tokens"],
                client["total_audio_seconds"],
                client["total_audio_minutes"],
                client["unique_voices_used"]
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=report_{report['period']}.csv"
            }
        )
    
    return report


# ============================================================
# 7. ADICIONE ESTA ROTA PARA SERVIR O DASHBOARD
# ============================================================

from fastapi.responses import FileResponse

@app.get("/dashboard.html")
async def serve_dashboard():
    """Serve o dashboard HTML"""
    return FileResponse("/home/francisco/talklabs/dashboard/index.html")

# ============================================================
# LOGGING CONFIGURATION (inicializada cedo)
# ============================================================

LOG_DIR = "/var/log/talklabs"
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except PermissionError:
    # fallback local se /var/log não for gravável
    LOG_DIR = os.path.expanduser("~/talklabs_logs")
    os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, "talklabs.log")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "%Y-%m-%d %H:%M:%S"
)

file_handler = RotatingFileHandler(LOG_PATH, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logging.info(f"✅ Logging inicializado em {LOG_PATH}")




# ------------------------------------------------------------
# CORS (permite acesso pelo frontend Lovable ou apps)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
