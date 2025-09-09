import time
from app.events.classification_events import finished, update_status
from app.extensions import socketio as sio


class ClassificationTask:
    @staticmethod
    def run(partnumber, socket_session_id, task_id):
        for i in range(5):
            time.sleep(2)
            print("classification_progress: ", i)

            update_status({
                "step": i + 1,
                "total": 5
            }, sid=socket_session_id)

        result = {
            "partnumber": partnumber,
            "classification": "1234.56.78",
            "status": "done",
            "task_id": task_id
        }
        finished(result, sid = socket_session_id)