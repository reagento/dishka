from abc import ABC, abstractmethod
from uuid import uuid4


class UUIDService(ABC):
    @abstractmethod
    def generate_uuid(self) -> str: ...


class UUIDServiceImpl(UUIDService):
    def generate_uuid(self) -> str:
        return str(uuid4())
