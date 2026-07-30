from dataclasses import dataclass


@dataclass
class ConversationTurn:
    role: str
    content: str
    created_at: str
