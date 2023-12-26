from typing import Optional, Dict

from pydantic import BaseModel

from schemas import ConnectedComputer, Lesson


class Context(BaseModel):
    lesson: Lesson
    connected_computers: Dict[int, ConnectedComputer] = {}


ctx = Context()
