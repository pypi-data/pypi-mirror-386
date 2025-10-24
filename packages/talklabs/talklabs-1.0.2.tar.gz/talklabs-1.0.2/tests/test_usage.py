"""
Script de teste para o sistema de contabilização de uso
Teste todas as funcionalidades do sistema

SALVAR COMO: /home/francisco/talklabs/tests/test_usage.py
"""

import requests
import json
import time

# Configurações
API_BASE = "http://localhost:5000"
API_KEY = "tlk_live_7GmR2xWzLqK8NpQf"

def test_text_to_speech():
    """Testa endpoint básico de TTS"""
    print("\n🎤 Testando Text-to-Speech...")
    
    url = f"{API_BASE}/v1/text-to-speech/yasmin_alves"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": "Olá! Este é um teste do sistema de contabilização de uso.",
        "model_id": "eleven_multilingual_v2",
        "language_code": "pt"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("✅ TTS funcionando")
        print(f"   - Duração: {response.headers.get('X-Audio-Duration', 'N/A')}s")
        print(f"   - Caracteres: {response.headers.get('X-Text-Characters', 'N/A')}")
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")


def test_get_usage():
    """Testa consulta de uso"""
    print("\n📊 Testando consulta de uso...")
    
    url = f"{API_BASE}/v1/usage"
    headers = {"xi-api-key": API_KEY}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        usage = response.json()
        print("✅ Uso consultado com sucesso:")
        print(f"   - Total de requisições: {usage['total_requests']}")
        print(f"   - Total de caracteres: {usage['total_characters']}")
        print(f"   - Total de tokens: {usage['total_tokens']}")
        print(f"   - Áudio gerado: {usage['total_audio_minutes']:.2f} minutos")
        print(f"   - Primeiro uso: {usage.get('first_use', 'N/A')}")
        print(f"   - Último uso: {usage.get('last_use', 'N/A')}")
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")


def test_usage_history():
    """Testa histórico de uso"""
    print("\n📜 Testando histórico de uso...")
    
    url = f"{API_BASE}/v1/usage/history?limit=5"
    headers = {"xi-api-key": API_KEY}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        history = data.get('history', [])
        print(f"✅ Histórico consultado: {len(history)} registros")
        
        for item in history[:3]:
            print(f"\n   📝 Requisição #{item['id']}:")
            print(f"      - Endpoint: {item['endpoint']}")
            print(f"      - Voz: {item['voice_id']}")
            print(f"      - Caracteres: {item['characters']}")
            print(f"      - Áudio: {item['audio_duration_seconds']}s")
            print(f"      - Data: {item['timestamp']}")
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")


def test_usage_stats():
    """Testa estatísticas por período"""
    print("\n📈 Testando estatísticas por período...")
    
    for period in ['day', 'week', 'month']:
        url = f"{API_BASE}/v1/usage/stats?period={period}"
        headers = {"xi-api-key": API_KEY}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', [])
            print(f"\n   📊 Estatísticas por {period}: {len(stats)} períodos")
            
            if stats:
                latest = stats[0]
                print(f"      - Período: {latest['period']}")
                print(f"      - Requisições: {latest['requests']}")
                print(f"      - Caracteres: {latest['characters']}")
                print(f"      - Áudio: {latest['audio_minutes']:.2f} min")
        else:
            print(f"   ❌ Erro ao consultar {period}: {response.status_code}")


def test_multiple_requests():
    """Faz múltiplas requisições para gerar dados"""
    print("\n🔄 Gerando múltiplas requisições de teste...")
    
    texts = [
        "Primeira frase de teste.",
        "Segunda frase um pouco maior para testar.",
        "Terceira frase ainda mais longa para simular uso real da API.",
        "Quarta frase com caracteres especiais: áçãoê!",
        "Quinta e última frase para completar os testes."
    ]
    
    url = f"{API_BASE}/v1/text-to-speech/yasmin_alves"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    for i, text in enumerate(texts, 1):
        print(f"   {i}/5 - Enviando: '{text[:30]}...'")
        data = {"text": text, "model_id": "eleven_multilingual_v2"}
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"      ✅ Sucesso")
        else:
            print(f"      ❌ Erro: {response.status_code}")
        
        time.sleep(0.5)  # Pequeno delay


def test_timestamps_endpoint():
    """Testa endpoint com timestamps"""
    print("\n⏱️ Testando endpoint com timestamps...")
    
    url = f"{API_BASE}/v1/text-to-speech/yasmin_alves/with-timestamps"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": "Teste de timestamps com várias palavras",
        "model_id": "eleven_multilingual_v2"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Timestamps gerados:")
        print(f"   - Duração: {data.get('audio_duration_seconds', 'N/A')}s")
        print(f"   - Caracteres: {data.get('characters_processed', 'N/A')}")
        print(f"   - Palavras com timestamps: {len(data.get('alignment', []))}")
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")


def run_all_tests():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 INICIANDO TESTES DO SISTEMA DE CONTABILIZAÇÃO")
    print("=" * 60)
    
    # Teste 1: Gera dados
    test_multiple_requests()
    time.sleep(1)
    
    # Teste 2: TTS básico
    test_text_to_speech()
    time.sleep(1)
    
    # Teste 3: TTS com timestamps
    test_timestamps_endpoint()
    time.sleep(1)
    
    # Teste 4: Consulta uso total
    test_get_usage()
    time.sleep(1)
    
    # Teste 5: Histórico
    test_usage_history()
    time.sleep(1)
    
    # Teste 6: Estatísticas
    test_usage_stats()
    
    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES CONCLUÍDOS!")
    print("=" * 60)
    print("\n💡 Acesse o dashboard em: http://localhost:5000/dashboard.html")


if __name__ == "__main__":
    run_all_tests()