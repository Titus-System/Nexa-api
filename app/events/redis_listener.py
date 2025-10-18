import json
import redis
from app.config import settings
from app.events.classification_events import batch_classification_finished_event, single_classification_finished_event
from app.events.events_enum import RedisChannelName
from app.core.logger_config import logger
from app.extensions import socketio
from app.schemas.classification_schemas import BatchClassificationResponse, SingleClassificationResponse, validate_and_get_model

class RedisListener:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
        self.logger = logger
        self.socket = socketio
        self.logger.info("📢 RedisListener inicializado e aguardando mensagens...")


    def start(self):
        for channel in RedisChannelName:
            self.pubsub.subscribe(channel.value)
        for message in self.pubsub.listen():
            try:
                channel = message["channel"].decode('utf-8')
                data = json.loads(message["data"])
                self._handle_channel(channel, data)
            except Exception as e:
                self.logger.error(f"ERRO no ouvinte Redis: {e}")
                continue


    def _handle_channel(self, channel: str, data: dict):
        if channel == RedisChannelName.TASK_RESULTS.value:
            self._handle_task_results(data)
        if channel == RedisChannelName.BATCH_TASK_DONE.value:
            self._handle_batch_task_done(data)


    def _handle_task_results(self, data: dict):
        room_id = data.pop("room_id", None)
        if not room_id:
            self.logger.error("room_id ausente nos dados de resultados da tarefa.")
            return

        self.logger.info(f"[INTERCEPTADO]: Resultado para a sala {room_id}. Resultado: {data.get('result')}")

        payload = validate_and_get_model(data, SingleClassificationResponse)
        single_classification_finished_event(payload, room_id)

        self.socket.close_room(room_id)

    def _handle_batch_task_done(self, data:dict):
        room_id = data.pop("room_id", None)
        if not room_id:
            self.logger.error("room_id ausente nos dados de resultados da tarefa.")
            return

        self.logger.info(f"[INTERCEPTADO]: Resultado para a sala {room_id}. Resultado: {data.get('result')}")

        payload = validate_and_get_model(data, BatchClassificationResponse)
        batch_classification_finished_event(payload, room_id)