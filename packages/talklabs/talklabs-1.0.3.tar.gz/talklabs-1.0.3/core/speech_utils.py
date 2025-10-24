"""
speech_utils.py
Camada auxiliar para pré e pós-processamento de texto e áudio (XTTS2 e outros modelos TTS).
"""

import re
import numpy as np
from num2words import num2words
import librosa
import datetime
from typing import List, Tuple, Optional
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

# ============================================================
# 🧹 TEXT PREPROCESSING
# ============================================================

def expand_abbreviations(text: str, custom_abbr: Optional[dict] = None) -> str:
    """
    Expande abreviações comuns para melhorar a leitura em TTS.
    
    Args:
        text: Texto a ser processado
        custom_abbr: Dicionário opcional com abreviações personalizadas
    
    Returns:
        Texto com abreviações expandidas
    """
    ABBREVIATIONS = {
        "Sr.": "Senhor",
        "Sra.": "Senhora",
        "Dr.": "Doutor",
        "Dra.": "Doutora",
        "R$": "reais",
        "%": "por cento",
        "etc.": "etcetera",
        "Ex.": "exemplo",
        "Av.": "avenida",
        "R.": "rua",
        "Tel.": "telefone",
        "e.g.": "por exemplo",
        "i.e.": "isto é",
        "Prof.": "Professor",
        "Profa.": "Professora",
        "Eng.": "Engenheiro",
        "Enga.": "Engenheira",
        "Ltd.": "Limitada",
        "S.A.": "Sociedade Anônima",
        "Ltda.": "Limitada",
        "CEP": "código de endereçamento postal",
        "CPF": "cépefê",
        "CNPJ": "cênepejota",
        "RG": "érrêgê",
        "km": "quilômetros",
        "m": "metros",
        "cm": "centímetros",
        "kg": "quilogramas",
        "g": "gramas",
        "ml": "mililitros",
        "l": "litros",
    }
    
    # Mescla abreviações personalizadas, se fornecidas
    if custom_abbr:
        ABBREVIATIONS.update(custom_abbr)
    
    for abbr, full in ABBREVIATIONS.items():
        # Usa regex com word boundary para evitar substituições parciais
        text = re.sub(r'\b' + re.escape(abbr) + r'\b', full, text, flags=re.IGNORECASE)
    
    return text


def normalize_numbers(text: str, lang: str = "pt") -> str:
    """
    Converte números inteiros em palavras para uma pronúncia natural.
    Agora suporta números decimais e números grandes.
    
    Args:
        text: Texto contendo números
        lang: Idioma para conversão (padrão: 'pt')
    
    Returns:
        Texto com números convertidos em palavras
    """
    # Normaliza números decimais (ex.: 3.14 -> "três vírgula quatorze")
    def decimal_repl(match):
        try:
            integer_part = int(match.group(1))
            decimal_part = match.group(2)
            integer_words = num2words(integer_part, lang=lang)
            decimal_words = " ".join([num2words(int(d), lang=lang) for d in decimal_part])
            return f"{integer_words} vírgula {decimal_words}"
        except Exception as e:
            logger.warning(f"Erro ao converter decimal {match.group()}: {e}")
            return match.group()
    
    text = re.sub(r"\b(\d+)[,.](\d+)\b", decimal_repl, text)
    
    # Normaliza números inteiros
    def int_repl(match):
        try:
            return num2words(int(match.group()), lang=lang)
        except Exception as e:
            logger.warning(f"Erro ao converter número {match.group()}: {e}")
            return match.group()
    
    text = re.sub(r"\b\d+\b", int_repl, text)
    return text


def normalize_currency(text: str, lang: str = "pt") -> str:
    """
    Normaliza valores monetários (ex.: R$ 150,50 -> "cento e cinquenta reais e cinquenta centavos").
    
    Args:
        text: Texto contendo valores monetários
        lang: Idioma para conversão
    
    Returns:
        Texto com valores monetários por extenso
    """
    def currency_repl(match):
        try:
            value = match.group(1).replace(".", "").replace(",", ".")
            real_part = int(float(value))
            cent_part = int((float(value) - real_part) * 100)
            
            result = num2words(real_part, lang=lang)
            result += " real" if real_part == 1 else " reais"
            
            if cent_part > 0:
                result += " e " + num2words(cent_part, lang=lang)
                result += " centavo" if cent_part == 1 else " centavos"
            
            return result
        except Exception as e:
            logger.warning(f"Erro ao converter moeda {match.group()}: {e}")
            return match.group()
    
    # Padrão: R$ 1.500,50 ou R$1500,50
    text = re.sub(r"R\$\s*([\d.,]+)", currency_repl, text)
    return text


def normalize_dates_and_times(text: str, lang: str = "pt") -> str:
    """
    Normaliza datas (ex.: 14/10/2025 -> "quatorze de outubro de dois mil e vinte e cinco")
    e horários (ex.: 14:30 -> "quatorze horas e trinta minutos") para TTS.
    
    Args:
        text: Texto contendo datas e horários
        lang: Idioma para conversão
    
    Returns:
        Texto com datas e horários por extenso
    """
    # Padrão para datas DD/MM/YYYY ou DD-MM-YYYY
    def date_repl(match):
        try:
            day, month, year = map(int, match.groups())
            months = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                      "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            
            if month < 1 or month > 12:
                return match.group()
            
            return f"{num2words(day, lang=lang)} de {months[month]} de {num2words(year, lang=lang)}"
        except Exception as e:
            logger.warning(f"Erro ao converter data {match.group()}: {e}")
            return match.group()
    
    text = re.sub(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_repl, text)

    # Padrão para horários HH:MM
    def time_repl(match):
        try:
            hour, minute = map(int, match.groups())
            if hour > 23 or minute > 59:
                return match.group()
            
            hour_str = num2words(hour, lang=lang) + " hora" + ("s" if hour != 1 else "")
            minute_str = " e " + num2words(minute, lang=lang) + " minuto" + ("s" if minute != 1 else "") if minute > 0 else ""
            return hour_str + minute_str
        except Exception as e:
            logger.warning(f"Erro ao converter horário {match.group()}: {e}")
            return match.group()
    
    text = re.sub(r"\b(\d{1,2}):(\d{2})\b", time_repl, text)
    
    return text


def normalize_ordinals(text: str, lang: str = "pt") -> str:
    """
    Converte ordinais (1º, 2ª) em palavras (primeiro, segunda).
    
    Args:
        text: Texto contendo ordinais
        lang: Idioma para conversão
    
    Returns:
        Texto com ordinais por extenso
    """
    def ordinal_repl(match):
        try:
            number = int(match.group(1))
            gender = match.group(2)
            ordinal = num2words(number, lang=lang, to='ordinal')
            
            # Ajusta gênero se necessário (simplificado)
            if gender in ['ª', 'a'] and ordinal.endswith('o'):
                ordinal = ordinal[:-1] + 'a'
            
            return ordinal
        except Exception as e:
            logger.warning(f"Erro ao converter ordinal {match.group()}: {e}")
            return match.group()
    
    text = re.sub(r"(\d+)[ºª°]", ordinal_repl, text)
    return text


def clean_punctuation(text: str) -> str:
    """
    Limpa e normaliza pontuação para evitar pausas artificiais em TTS.
    
    Args:
        text: Texto a ser limpo
    
    Returns:
        Texto com pontuação normalizada
    """
    text = text.replace("...", "…")
    text = re.sub(r"\s*\.\s*", ". ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"([!?])([A-Za-zÀ-ÿ])", r"\1 \2", text)
    text = re.sub(r"\s+", " ", text.strip())
    
    # Remove pontuação duplicada
    text = re.sub(r"([.!?]){2,}", r"\1", text)
    
    return text


def remove_special_chars(text: str, keep_chars: str = "") -> str:
    """
    Remove caracteres especiais ou emojis que podem confundir o TTS.
    Mantém apenas letras, números e pontuação básica.
    
    Args:
        text: Texto a ser limpo
        keep_chars: Caracteres adicionais a manter (opcional)
    
    Returns:
        Texto sem caracteres especiais
    """
    # Remove emojis e símbolos não alfanuméricos, exceto pontuação comum
    pattern = r"[^\w\s\.,!?;:()'\"-" + re.escape(keep_chars) + r"]"
    text = re.sub(pattern, "", text)
    return text


def sanitize_tts_text(text: str) -> str:
    """
    Remove casos em que o XTTS leria 'ponto', 'vírgula', etc.
    
    Args:
        text: Texto a ser sanitizado
    
    Returns:
        Texto sanitizado
    """
    text = text.replace(" .", ".")
    text = text.replace(" ,", ",")
    text = text.replace(" ponto ", " ")
    text = text.replace(" vírgula ", " ")
    text = text.replace(" ;", ";")
    text = text.replace(" :", ":")
    
    # Remove espaços antes de pontuação
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    
    return text


def split_text_into_chunks(text: str, max_len: int = 300, respect_sentences: bool = True) -> List[str]:
    """
    Divide texto em blocos curtos preservando pausas naturais (pontos, exclamações, etc.).
    
    Args:
        text: Texto a ser dividido
        max_len: Comprimento máximo de cada chunk
        respect_sentences: Se True, nunca quebra no meio de uma frase
    
    Returns:
        Lista de chunks de texto
    """
    if not respect_sentences:
        # Divisão simples por comprimento
        return [text[i:i+max_len] for i in range(0, len(text), max_len)]
    
    sentences = re.split(r'(?<=[.!?…])\s+', text)
    chunks, current = [], ""
    
    for s in sentences:
        if len(current) + len(s) + 1 < max_len:
            current += " " + s if current else s
        else:
            if current:
                chunks.append(current.strip())
            # Se uma sentença sozinha for maior que max_len, divide ela
            if len(s) > max_len:
                words = s.split()
                temp = ""
                for word in words:
                    if len(temp) + len(word) + 1 < max_len:
                        temp += " " + word if temp else word
                    else:
                        chunks.append(temp.strip())
                        temp = word
                current = temp
            else:
                current = s
    
    if current:
        chunks.append(current.strip())
    
    return [c for c in chunks if c]  # Remove chunks vazios


def prepare_text(text: str, lang: str = "pt", expand_currency: bool = True, 
                 expand_ordinals: bool = True, custom_abbr: Optional[dict] = None) -> str:
    """
    Pipeline completo de pré-processamento.
    
    Args:
        text: Texto a ser preparado
        lang: Idioma para conversão
        expand_currency: Se True, expande valores monetários
        expand_ordinals: Se True, expande números ordinais
        custom_abbr: Abreviações personalizadas
    
    Returns:
        Texto preparado para TTS
    """
    if not text or not text.strip():
        return ""
    
    text = expand_abbreviations(text, custom_abbr)
    
    if expand_currency:
        text = normalize_currency(text, lang)
    
    if expand_ordinals:
        text = normalize_ordinals(text, lang)
    
    text = normalize_dates_and_times(text, lang)
    text = normalize_numbers(text, lang)
    text = remove_special_chars(text)
    text = clean_punctuation(text)
    text = sanitize_tts_text(text)
    
    return text.strip()


# ============================================================
# 🔊 AUDIO POST-PROCESSING
# ============================================================

def trim_silence(wav: np.ndarray, threshold_db: float = -40.0, 
                 frame_length: int = 2048, hop_length: int = 512) -> np.ndarray:
    """
    Remove silêncios iniciais e finais do áudio para um resultado mais limpo.
    
    Args:
        wav: Array numpy com áudio
        threshold_db: Limiar de silêncio em dB
        frame_length: Tamanho do frame para análise
        hop_length: Passo entre frames
    
    Returns:
        Áudio sem silêncios nas extremidades
    """
    try:
        wav_trimmed, _ = librosa.effects.trim(
            wav, 
            top_db=-threshold_db, 
            frame_length=frame_length, 
            hop_length=hop_length
        )
        return wav_trimmed
    except Exception as e:
        logger.warning(f"Erro ao remover silêncio: {e}")
        return wav


def normalize_audio(wav: np.ndarray, target_db: float = -14.0) -> np.ndarray:
    """
    Normaliza RMS do áudio para um nível consistente.
    
    Args:
        wav: Array numpy com áudio
        target_db: Nível RMS alvo em dB
    
    Returns:
        Áudio normalizado
    """
    rms = np.sqrt(np.mean(wav ** 2))
    if rms < 1e-9:
        logger.warning("Áudio muito baixo ou silencioso, não foi normalizado")
        return wav
    
    scalar = 10 ** (target_db / 20) / rms
    return np.clip(wav * scalar, -1.0, 1.0)


def adjust_speed(wav: np.ndarray, rate: float = 1.0, sr: int = 22050) -> np.ndarray:
    """
    Ajusta velocidade do áudio (pitch-preserving).
    
    Args:
        wav: Array numpy com áudio
        rate: Taxa de velocidade (1.0 = normal, >1.0 = mais rápido, <1.0 = mais lento)
        sr: Sample rate do áudio
    
    Returns:
        Áudio com velocidade ajustada
    """
    if rate == 1.0 or rate <= 0:
        return wav
    
    try:
        return librosa.effects.time_stretch(wav.astype(np.float32), rate=rate)
    except Exception as e:
        logger.warning(f"Erro ao ajustar velocidade: {e}")
        return wav


def apply_fade(wav: np.ndarray, fade_in_ms: int = 50, fade_out_ms: int = 100, 
               sr: int = 22050) -> np.ndarray:
    """
    Aplica fade in/out para suavizar início e fim do áudio.
    
    Args:
        wav: Array numpy com áudio
        fade_in_ms: Duração do fade in em milissegundos
        fade_out_ms: Duração do fade out em milissegundos
        sr: Sample rate do áudio
    
    Returns:
        Áudio com fade aplicado
    """
    fade_in_samples = int(fade_in_ms * sr / 1000)
    fade_out_samples = int(fade_out_ms * sr / 1000)
    
    if len(wav) < fade_in_samples + fade_out_samples:
        return wav
    
    # Fade in
    fade_in_curve = np.linspace(0, 1, fade_in_samples)
    wav[:fade_in_samples] *= fade_in_curve
    
    # Fade out
    fade_out_curve = np.linspace(1, 0, fade_out_samples)
    wav[-fade_out_samples:] *= fade_out_curve
    
    return wav


def remove_dc_offset(wav: np.ndarray) -> np.ndarray:
    """
    Remove DC offset (componente contínuo) do áudio.
    
    Args:
        wav: Array numpy com áudio
    
    Returns:
        Áudio sem DC offset
    """
    return wav - np.mean(wav)


def apply_compression(wav: np.ndarray, threshold: float = 0.5, 
                      ratio: float = 4.0) -> np.ndarray:
    """
    Aplica compressão dinâmica simples ao áudio.
    
    Args:
        wav: Array numpy com áudio
        threshold: Limiar de compressão (0-1)
        ratio: Taxa de compressão
    
    Returns:
        Áudio comprimido
    """
    compressed = np.copy(wav)
    mask = np.abs(wav) > threshold
    compressed[mask] = np.sign(wav[mask]) * (
        threshold + (np.abs(wav[mask]) - threshold) / ratio
    )
    return compressed


def postprocess_audio(wav: np.ndarray, speed: float = 1.0, normalize: bool = True, 
                     trim: bool = True, fade: bool = True, remove_dc: bool = True,
                     compress: bool = False, sr: int = 22050) -> np.ndarray:
    """
    Aplica ajustes finais no áudio.
    
    Args:
        wav: Array numpy com áudio
        speed: Taxa de velocidade
        normalize: Se True, normaliza o áudio
        trim: Se True, remove silêncios
        fade: Se True, aplica fade in/out
        remove_dc: Se True, remove DC offset
        compress: Se True, aplica compressão dinâmica
        sr: Sample rate do áudio
    
    Returns:
        Áudio pós-processado
    """
    if len(wav) == 0:
        return wav
    
    if remove_dc:
        wav = remove_dc_offset(wav)
    
    if trim:
        wav = trim_silence(wav)
    
    if compress:
        wav = apply_compression(wav)
    
    if normalize:
        wav = normalize_audio(wav)
    
    if speed != 1.0:
        wav = adjust_speed(wav, rate=speed, sr=sr)
    
    if fade:
        wav = apply_fade(wav, sr=sr)
    
    return wav


# ============================================================
# 🎯 HELPER FUNCTIONS
# ============================================================

def validate_audio(wav: np.ndarray, sr: int = 22050, 
                  min_duration_ms: int = 100) -> Tuple[bool, str]:
    """
    Valida se o áudio tem características aceitáveis.
    
    Args:
        wav: Array numpy com áudio
        sr: Sample rate
        min_duration_ms: Duração mínima em milissegundos
    
    Returns:
        Tupla (é_válido, mensagem)
    """
    if len(wav) == 0:
        return False, "Áudio vazio"
    
    duration_ms = len(wav) / sr * 1000
    if duration_ms < min_duration_ms:
        return False, f"Áudio muito curto ({duration_ms:.0f}ms < {min_duration_ms}ms)"
    
    if np.all(wav == 0):
        return False, "Áudio contém apenas silêncio"
    
    if np.any(np.isnan(wav)) or np.any(np.isinf(wav)):
        return False, "Áudio contém valores inválidos (NaN ou Inf)"
    
    return True, "Áudio válido"


def estimate_audio_quality(wav: np.ndarray, sr: int = 22050) -> dict:
    """
    Estima métricas de qualidade do áudio.
    
    Args:
        wav: Array numpy com áudio
        sr: Sample rate
    
    Returns:
        Dicionário com métricas de qualidade
    """
    return {
        "duration_s": len(wav) / sr,
        "rms": float(np.sqrt(np.mean(wav ** 2))),
        "peak": float(np.max(np.abs(wav))),
        "dc_offset": float(np.mean(wav)),
        "zero_crossings": int(np.sum(np.abs(np.diff(np.sign(wav)))) / 2),
        "dynamic_range_db": float(20 * np.log10(np.max(np.abs(wav)) / (np.mean(np.abs(wav)) + 1e-9)))
    }