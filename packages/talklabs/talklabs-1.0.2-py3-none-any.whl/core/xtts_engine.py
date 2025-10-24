import io
import os
import torch
from torch.serialization import add_safe_globals
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
import logging
import soundfile as sf
import numpy as np
import librosa
import glob
from core.speech_utils import prepare_text, postprocess_audio, split_text_into_chunks  # ✅ caminho correto
import re
from supabase import create_client
import requests


def prepare_text(text: str, lang="pt"):
    """
    Limpa e normaliza o texto antes de enviar ao modelo TTS.
    """
    # Remove múltiplos espaços
    text = re.sub(r"\s+", " ", text.strip())

    # Substitui reticências e pontos isolados por pausas naturais
    text = re.sub(r"\.{2,}", "…", text)
    
    # Evita o modelo ler o ponto literal — substitui por vírgula
    text = text.replace(".", ",")
    
    # Remove espaços antes de pontuação
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    return text.strip()

def split_text_into_chunks(text, max_length=250):
    """
    Divide o texto em sentenças sem separar pontuação isolada.
    """
    # Divide mantendo a pontuação junto à frase
    parts = re.split(r'(?<=[.!?])\s+', text)
    chunks = []

    current = ""
    for sentence in parts:
        if len(current) + len(sentence) < max_length:
            current += (" " + sentence).strip()
        else:
            chunks.append(current.strip())
            current = sentence
    if current:
        chunks.append(current.strip())

    # Remove possíveis blocos que sejam só pontuação
    chunks = [c for c in chunks if not re.fullmatch(r'[^\w]+', c)]
    return chunks





# Libera classes internas necessárias para o modelo XTTS2
add_safe_globals([XttsConfig])


class TalkLabsEngine:
    """Camada de síntese de fala TalkLabs (XTTS2) com suporte multilíngue."""

    def __init__(self, model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
        # ============================================================
        # 🧠 Seleção de dispositivo
        # ============================================================
        if torch.cuda.is_available():
            try:
                gpu_name = torch.cuda.get_device_name(0)
                logging.info(f"[TalkLabs] ⚡ GPU detectada: {gpu_name}")
                if "5090" in gpu_name:
                    print("[TalkLabs] ⚠️ PyTorch ainda não suporta RTX 5090 nativamente — fallback genérico CUDA.")
                self.device = "cuda"
            except Exception:
                self.device = "cuda"
        else:
            self.device = "cpu"
            print("[TalkLabs] ⚠️ Nenhuma GPU detectada, usando CPU.")

        # ============================================================
        # 🎛️ Inicialização do modelo
        # ============================================================
        print(f"[TalkLabs] Inicializando XTTS2 ({model_name}) em {self.device}...")
        try:
            self.model = TTS(model_name).to(self.device)
            print(f"[TalkLabs] ✅ Modelo XTTS2 carregado com sucesso ({self.device}).")
        except Exception as e:
            print(f"[TalkLabs] ❌ Erro ao carregar modelo XTTS2: {e}")
            raise

        # ============================================================
        # 🔊 Registro de amostras locais
        # ============================================================
        self.speakers = {}
        self._sync_from_supabase()
        print("[TalkLabs] 🔁 Chamando sincronização com Supabase...")


    def _sync_from_supabase(self):
        """Baixa e registra todas as vozes ativas do Supabase."""
        logging.info("[TalkLabs] 🔄 Sincronizando vozes do Supabase...")

        try:
            # Conexão com o Supabase
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            supabase = create_client(supabase_url, supabase_key)

            # Busca vozes ativas
            result = supabase.table("talklabs_voices").select("*").eq("is_active", True).execute()
            voices = result.data or []

            if not voices:
                logging.warning("[TalkLabs] ⚠️ Nenhuma voz ativa encontrada no Supabase.")
                return

            # Diretório de cache local
            cache_dir = "/home/francisco/talklabs/cache/voices"
            os.makedirs(cache_dir, exist_ok=True)

            # Baixa e registra cada voz
            for v in voices:
                voice_id = v["voice_id"]
                sample_url = v["sample_url"]
                file_name = voice_id.replace("/", "_") + ".wav"
                local_path = os.path.join(cache_dir, file_name)

                # Baixa apenas se não existir no cache
                if not os.path.exists(local_path):
                    try:
                        r = requests.get(sample_url, timeout=15)
                        r.raise_for_status()
                        with open(local_path, "wb") as f:
                            f.write(r.content)
                        logging.info(f"[TalkLabs] ✅ Voz baixada: {voice_id}")
                    except Exception as e:
                        logging.error(f"[TalkLabs] ❌ Falha ao baixar {voice_id}: {e}")
                        continue

                # Registra a voz no mecanismo
                self.speakers.setdefault(voice_id, []).append(local_path)

            logging.info(f"[TalkLabs] 🔊 {len(self.speakers)} vozes registradas do Supabase.")

        except Exception as e:
            logging.error(f"[TalkLabs] ❌ Erro na sincronização de vozes: {e}")


    # ============================================================
    # 📂 Carrega amostras automaticamente (com suporte a idiomas)
    # ============================================================
    def _load_samples(self):
        """
        Carrega amostras de voz no formato:
        /samples/<idioma>/<voz>/<amostra>.wav
        Exemplo:
        /samples/pt-br/adam_rocha/adam_rocha.wav
        """
        base_dir = "/home/francisco/talklabs/samples"
        if not os.path.exists(base_dir):
            print(f"[TalkLabs] ⚠️ Diretório de amostras não encontrado ({base_dir})")
            return

        count = 0
        for wav_path in glob.glob(os.path.join(base_dir, "**", "*.wav"), recursive=True):
            parts = wav_path.split(os.sep)

            # Busca padrão /samples/<idioma>/<voz>/<arquivo.wav>
            try:
                lang = parts[-3]
                speaker = parts[-2]
            except IndexError:
                continue

            # Aceita apenas pastas no formato xx-xx
            if not (len(lang) == 5 and lang[2] == "-"):
                lang = "unknown"

            voice_id = f"{lang}/{speaker}"
            self.speakers.setdefault(voice_id, []).append(wav_path)
            count += 1

        print(f"[TalkLabs] 🔍 {count} amostras carregadas no total.")
        for spk, files in self.speakers.items():
            print(f"[TalkLabs] 🔊 Voz '{spk}' registrada com {len(files)} amostras.")

    # ============================================================
    # 🧠 Síntese de fala
    # ============================================================
    def synthesize(
        self,
        text: str,
        speaker: str = None,
        language: str = "pt",
        speed: float = 1.0,
        temperature: float = 0.75
    ):
        """
        Gera áudio WAV a partir de texto.
        - speaker deve estar no formato: <idioma>/<voz>
        """
        print(f"[TalkLabs] 🗣️ Texto: '{text[:60]}...' (voz={speaker}, idioma={language})")

        if speaker and speaker not in self.speakers:
            available = ", ".join(list(self.speakers.keys())[:5])
            raise ValueError(
                f"❌ Voz '{speaker}' não registrada.\n"
                f"Verifique se existe /samples/<idioma>/<voz> com amostras .wav\n"
                f"Exemplo: /samples/pt-br/adam_rocha/adam_rocha.wav\n"
                f"Disponíveis: {available}..."
            )

        try:
            # ============================================================
            # 🎧 Seleciona amostra de voz (speaker)
            # ============================================================
            ref_wav_path = None
            if speaker:
                ref_wav_path = self.speakers[speaker][0]
                print(f"[TalkLabs] 🎧 Amostra carregada: {ref_wav_path}")

            # ============================================================
            # 🧹 Pré-processamento de texto
            # ============================================================
            # Usa módulo auxiliar speech_utils.py
            

            print("[TalkLabs] 🔍 Pré-processando texto...")
            text = prepare_text(text, lang=language)
            sentences = split_text_into_chunks(text)

            print(f"[TalkLabs] 🧾 Texto dividido em {len(sentences)} blocos.")

            # ============================================================
            # 🧮 Geração neural por blocos (melhor estabilidade)
            # ============================================================
            wav_segments = []
            for i, segment_text in enumerate(sentences, start=1):
                print(f"[TalkLabs] 🎙️ Gerando bloco {i}/{len(sentences)}: {segment_text[:50]}...")
                segment_audio = self.model.tts(
                    text=segment_text,
                    speaker_wav=ref_wav_path,
                    language=language
                )
                wav_segments.append(segment_audio)

            # Concatena blocos de áudio
            wav = np.concatenate(wav_segments)

            # ============================================================
            # 🎚️ Pós-processamento de áudio (limpeza, normalização, velocidade)
            # ============================================================
            print("[TalkLabs] 🎚️ Aplicando pós-processamento de áudio...")
            wav = postprocess_audio(wav, speed=speed, normalize=True, trim=True)

            # ============================================================
            # 💾 Conversão para WAV em bytes
            # ============================================================
            buf = io.BytesIO()
            sf.write(buf, wav, samplerate=24000, format="WAV")
            buf.seek(0)

            print("[TalkLabs] ✅ Fala gerada com sucesso.")
            return buf.read()

        except Exception as e:
            print(f"[TalkLabs] ❌ Erro na síntese: {e}")
            raise
