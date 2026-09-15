from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class ConversationSummary(BaseModel):
    conversation_id: UUID
    other_user_id: UUID
    other_user_name: str
    last_message: Optional[str]
    last_message_at: Optional[datetime]