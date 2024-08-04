from typing import Protocol
from uuid import uuid4


class UUIDService(Protocol):
    def generate_uuid(self) -> str: ...


class UUIDServiceImpl:
    def generate_uuid(self) -> str:
        return str(uuid4())
