from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    hotels: Optional[List[dict]] = None
    flights: Optional[List[dict]] = None