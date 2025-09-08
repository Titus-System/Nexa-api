import logging
import os
import json
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from queue import Queue
from datetime import datetime

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    # fallback simples caso colorama não esteja instalada
    class Fore:
        RED = "\033[91m"
        YELLOW = "\033[93m"
        GREEN = "\033[92m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
    class Style:
        BRIGHT = "\033[1m"
        RESET_ALL = "\033[0m"


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": record.getMessage(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.CYAN + Style.BRIGHT,
        logging.INFO: Fore.GREEN + Style.BRIGHT,
        logging.WARNING: Fore.YELLOW + Style.BRIGHT,
        logging.ERROR: Fore.RED + Style.BRIGHT,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        reset = Style.RESET_ALL

        return (
            f"{color}[{record.levelname}] {record.module}.{record.funcName}:{record.lineno} "
            f"- {record.getMessage()}{reset}"
        )


class AsyncLogger:
    def __init__(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")

        json_formatter = JsonFormatter()
        console_formatter = ConsoleFormatter()

        max_file_size = 10 * 1024 * 1024  # 10MB
        backup_count = 5

        # Handlers de arquivo (JSON)
        file_handler = RotatingFileHandler(
            "logs/app.json", maxBytes=max_file_size, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(logging.INFO)

        error_handler = RotatingFileHandler(
            "logs/error.json", maxBytes=max_file_size, backupCount=backup_count, encoding="utf-8"
        )
        error_handler.setFormatter(json_formatter)
        error_handler.setLevel(logging.ERROR)

        # Console (human-readable + colorido)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(console_formatter)
        stream_handler.setLevel(logging.DEBUG)

        # Fila centralizada
        self.log_queue = Queue(-1)
        queue_handler = QueueHandler(self.log_queue)

        # Logger principal
        self.logger = logging.getLogger("app")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(queue_handler)

        # Listener roda em thread separada
        self.listener = QueueListener(
            self.log_queue,
            file_handler,
            error_handler,
            stream_handler,
        )
        self.listener.start()

    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, stacklevel=2, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, stacklevel=2, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, stacklevel=2, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self.logger.error(message, stacklevel=2, *args, **kwargs)

    def stop(self):
        self.listener.stop()


logger = AsyncLogger()
