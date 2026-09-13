from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chat import Chat


@dataclass
class Message:
    id: int
    text: str
    chat: "Chat"