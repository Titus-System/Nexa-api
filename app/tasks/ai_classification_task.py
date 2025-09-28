import json
import uuid
from celery import Task
import requests
from celery.result import AsyncResult
from app.events.events_enum import EventName
from app.extensions import celery
from app.schemas.ai_schemas import AISingleClassificationRequest
from app.schemas.classification_schemas import FailedStatusResponse, StartSingleClassificationSchema, UpdateStatusResponse, validate_and_get_model
from app.services.protocols import IAsyncTaskClient
from . import external_socketio, celery_logger, redis_client
from app.config import settings


class CeleryTaskClientAI(IAsyncTaskClient):
    def run_single_classification_task(self, task_data:StartSingleClassificationSchema):
        task: AsyncResult = ai_classification_task.delay(task_data.model_dump(exclude_none=True))
        return task.id


@celery.task(bind=True)
def ai_classification_task(self: Task, task_data: dict):
    task_id = self.request.id
    progress_channel = f"progress-{uuid.uuid4()}"
    
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(progress_channel)
    celery_logger.info(f"Ouvindo o canal de progresso: {progress_channel}")
    
    room_id = task_data.pop("room_id")
    partnumber = task_data.get("partnumber")

    request_data = AISingleClassificationRequest(
        **task_data,
        progress_channel=progress_channel
    )
    job_id = _initiate_remote_job(request_data, room_id)
    
    if not job_id:
        pubsub.unsubscribe(progress_channel)
        celery_logger.warning(f"Desinscrito do canal {progress_channel} devido à falha na iniciação do job.")
        return
    
    finished_payload = None
    try:
        finished_payload = _listen_for_progress(pubsub, room_id)
    finally:
        pubsub.unsubscribe(progress_channel)
        celery_logger.info(f"Desinscrito do canal de progresso: {progress_channel}")

    if finished_payload:
        _publish_final_result(finished_payload, room_id, partnumber)
    
    return finished_payload


def _initiate_remote_job(request_data: AISingleClassificationRequest, room_id: str) -> str | None:
    try:
        response = requests.post(
            f"{settings.NEXA_AI_SERVER}/process/single_partnumber",
            json = request_data.model_dump()
        )
        celery_logger.info(f"Requisição POST enviada para {settings.NEXA_AI_SERVER}/process_single_partnumber. Status code: {response.status_code}")
        response.raise_for_status()
        job_id = response.json()['job_id']
        celery_logger.info(f"Iniciado job de processamento externo com ID: {job_id}")
        return job_id
    except requests.RequestException as e:
        celery_logger.error(f"Falha ao iniciar job externo: {e}")

        external_socketio.emit(
            EventName.CLASSIFICATION_UPDATE_STATUS.value,
            {
                "status": "failed",
                "message": "Erro ao iniciar o processamento do partnumber.",
            },
            to=room_id
        )
        
        return None


def _listen_for_progress(pubsub, room_id: str) -> dict | None:
    """Ouve o canal de progresso e processa as mensagens recebidas."""
    finished_payload = None
    for message in pubsub.listen():
        try:
            data = json.loads(message['data'])
            status = data.get('status')

            if status == 'processing':
                progress_payload = data.get('progress', {})
                celery_logger.info(f"\n[PROGRESS] Progresso recebido: {progress_payload}\n")
                progress_payload['status'] = 'processing'
                progress_payload = validate_and_get_model(progress_payload, UpdateStatusResponse).model_dump(exclude_none=True)
                external_socketio.emit(
                    EventName.CLASSIFICATION_UPDATE_STATUS.value,
                    progress_payload, 
                    to=room_id
                )
            elif status == 'failed':
                fail_payload = {
                    'status': 'failed',
                    'message': data.get('error', 'O processamento falhou sem mensagem de erro.')
                }
                fail_payload = validate_and_get_model(fail_payload, FailedStatusResponse).model_dump(exclude_none=True)

                external_socketio.emit(
                    EventName.CLASSIFICATION_UPDATE_STATUS.value,
                    fail_payload,
                    to=room_id
                )
                celery_logger.error(f"Job externo falhou: {data.get('error')}")

            elif status == 'done':
                celery_logger.info("Recebida mensagem de conclusão do job.")
                finished_payload = {
                    "status": "done",
                    "message": "Processamento concluído com sucesso.",
                    "result": data.get('result', {})
                }
                break
        except (json.JSONDecodeError, TypeError) as e:
            celery_logger.warning(f"Erro ao processar mensagem do Redis: {e}")
    return finished_payload


def _publish_final_result(payload: dict, room_id: str, partnumber: str):
    """Publica o resultado final no canal principal para interceptação."""
    payload['partnumber'] = partnumber
    payload['room_id'] = room_id
    celery_logger.info(f"\n\n[PUBLISH] redis publish payload: {payload}\n\n")
    redis_client.publish('task_results', json.dumps(payload))
    celery_logger.info(f"\n\nResultado final para a sala {room_id} publicado com sucesso.\n\n")





# 1.  **Worker Celery (Iniciador):**
#     * Cria um nome de canal único (ex: `'progress-123'`).
#     * Faz a requisição `POST` para o Servidor de Processamento, enviando os dados da tarefa **E** o nome do canal `'progress-123'`.

# 2.  **Worker Celery (Ouvinte):**
#     * Imediatamente após a requisição `POST`, ele se **INSCREVE** (`SUBSCRIBE`) no canal `'progress-123'`.
#     * Ele entra em modo de escuta, aguardando mensagens *nesse canal*.

# 3.  **Servidor de Processamento (O "Falante"):**
#     * Recebe a requisição, pega os dados do trabalho e o nome do canal.
#     * Começa o trabalho pesado.
#     * A cada passo importante, ele **PUBLICA** (`PUBLISH`) uma mensagem de progresso *para* o canal `'progress-123'`. Ele nunca se inscreve, apenas "fala" para o canal.

# 4.  **Worker Celery (Receptor e Repassador):**
#     * Enquanto está inscrito, ele recebe as mensagens que o Servidor de Processamento publica.
#     * Para cada mensagem de progresso recebida, ele a retransmite (`socketio.emit`) para o frontend do usuário.

# 5.  **Finalização:**
#     * O Servidor de Processamento termina o trabalho e **PUBLICA** a mensagem final (`"status": "done"`) no canal `'progress-123'`.
#     * O Worker Celery recebe esta mensagem final.
#     * Ele se **DESINSCREVE** (`UNSUBSCRIBE`) do canal `'progress-123'`.
#     * Por fim, ele **PUBLICA** o resultado final e limpo no canal principal da aplicação (`'classification_results'`), como já fazia antes.


#Comunicação híbrida: HTTP REST + Redis Pub/Sub
# A comunicação entre o orquestrador (Worker Celery) e o executor (Servidor de Processamento) utiliza um padrão de comunicação híbrido. 
# A iniciação da tarefa é feita através de um canal de controle síncrono via API REST (HTTP POST), 
# enquanto o retorno de dados de progresso e o resultado final ocorrem por um canal de notificação assíncrono, 
# implementado com o padrão Publish/Subscribe sobre um message broker Redis. 
# Este design combina a simplicidade do REST para iniciar jobs com a eficiência e escalabilidade do Pub/Sub para a comunicação em tempo real.