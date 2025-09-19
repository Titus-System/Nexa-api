"""
Teste de integração completo para o serviço de classificação.

Este teste verifica o seguinte fluxo:
1.  Um cliente se conecta ao servidor via Socket.IO.
2.  O cliente entra em uma "sala" nomeada com o partnumber de interesse.
3.  O cliente faz uma requisição HTTP POST para iniciar a tarefa de classificação.
4.  O servidor aceita a requisição e enfileira a tarefa no Celery.
5.  O worker do Celery processa a tarefa.
6.  Ao concluir, o worker emite um evento Socket.IO para a sala específica.
7.  O teste confirma que o cliente na sala recebeu o evento com os dados corretos.
"""
import requests
import socketio
import threading
import time
import pytest

BASE_URL = "http://localhost:5000"
PARTNUMBER_PARA_TESTAR = "PN-FINAL-TEST-789"
CELERY_TIMEOUT = 20

classification_finished_event = threading.Event()
calssification_error_event = threading.Event()

event_data = {}


sio = socketio.Client()

@sio.event
def connect():
    print(f"\n✅ Cliente conectado com sucesso! SID: {sio.sid}")

@sio.event
def disconnect():
    print("\n❌ Cliente desconectado.")


@sio.on("classification_update_status")
def on_classification_progress(data):
    if data.get('error'):
        print(f"\n❌ Erro na classificação: {data['error']}")
        disconnect()
        calssification_error_event.set()

    print(f"\n🔄 Progresso da classificação: {data}")



@sio.on('classification_finished')
def on_classification_finished(data):
    global event_data
    print(f"\n✅ Evento 'classification_finished' recebido: {data}")
    event_data = data

    # Avisa a thread principal do teste que o evento chegou e ela pode continuar.
    classification_finished_event.set()


# --- O Teste Principal ---
def test_full_classification_flow_with_room_architecture():
    """
    Executa o teste de integração de ponta a ponta.
    """
    try:
        print(f"▶️ Tentando conectar ao servidor em {BASE_URL}...")
        sio.connect(BASE_URL, transports=['websocket'])
        assert sio.connected


        payload = {"partnumber": PARTNUMBER_PARA_TESTAR}
        print(f"▶️ Enviando requisição POST para {BASE_URL}/classify-partnumber com payload: {payload}")
        response = requests.post(f"{BASE_URL}/classify-partnumber", json=payload)

        assert response.status_code == 202, f"Esperava status 202, mas recebeu {response.status_code}. Resposta: {response.text}"
        post_data = response.json()
        assert "room_id" in post_data
        room_id = post_data["room_id"]
        print(f"✅ [POST /classify] Resposta 202 OK recebida. Task ID: {post_data['task_id']}")

        print(f"▶️ Emitindo evento 'join' para a sala: {room_id}")
        sio.emit('join', {'room_id': room_id})
        time.sleep(1)

        error_received = calssification_error_event.wait(timeout=1)

        if not error_received:
            print(f"⏳ Aguardando a notificação do Celery por até {CELERY_TIMEOUT} segundos...")
            event_received = classification_finished_event.wait(timeout=CELERY_TIMEOUT)

            assert event_received, f"❌ ERRO: Timeout! O evento 'classification_finished' não foi recebido após {CELERY_TIMEOUT} segundos."

            assert event_data.get('partnumber') == PARTNUMBER_PARA_TESTAR
            assert event_data.get('status') == 'done'
            print("✅ Dados recebidos no evento estão corretos!")
        else:
            assert False, "❌ ERRO: Recebido erro de classificação via Socket.IO."

    finally:
        if sio.connected:
            sio.disconnect()