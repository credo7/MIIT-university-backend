from typing import Optional

from pydantic import BaseModel


class SharedState(BaseModel):
    lesson_id: Optional[int]


shared_state = SharedState()
