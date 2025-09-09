from typing import Protocol


class ClassificationServiceProtocol(Protocol):
    @staticmethod
    def start_classification(schema):
        ...
