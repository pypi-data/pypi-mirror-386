from enum import Enum
from typing import List, Literal, Union

from pydantic import BaseModel

"""Type definitions for Dojo."""


class ActionType(str, Enum):
    KEY = "key"
    CLICK = "click"
    RIGHT_CLICK = "right_click"
    SCROLL = "scroll"
    TYPE = "type"
    DOUBLE_CLICK = "double_click"
    DRAG = "drag"
    MOVE_TO = "move_to"
    PRESS = "press"
    HOTKEY = "hotkey"
    MIDDLE_CLICK = "middle_click"
    DONE = "done"
    WAIT = "wait"
    FAIL = "fail"


class KeyAction(BaseModel):
    type: Literal[ActionType.KEY]
    key: str


class ClickAction(BaseModel):
    type: Literal[ActionType.CLICK]
    x: int
    y: int


class RightClickAction(BaseModel):
    type: Literal[ActionType.RIGHT_CLICK]
    x: int
    y: int


class ScrollAction(BaseModel):
    type: Literal[ActionType.SCROLL]
    direction: str = "up"
    amount: int = 100


class TypeAction(BaseModel):
    type: Literal[ActionType.TYPE]
    text: str


class DoubleClickAction(BaseModel):
    type: Literal[ActionType.DOUBLE_CLICK]
    x: int
    y: int


class DragAction(BaseModel):
    type: Literal[ActionType.DRAG]
    from_x: int
    from_y: int
    to_x: int
    to_y: int
    duration: float = 1.0


class MoveToAction(BaseModel):
    type: Literal[ActionType.MOVE_TO]
    x: int
    y: int
    duration: float = 0.0


class PressAction(BaseModel):
    type: Literal[ActionType.PRESS]
    key: str


class HotkeyAction(BaseModel):
    type: Literal[ActionType.HOTKEY]
    keys: List[str]


class MiddleClickAction(BaseModel):
    type: Literal[ActionType.MIDDLE_CLICK]
    x: int
    y: int


class DoneAction(BaseModel):
    type: Literal[ActionType.DONE]


class WaitAction(BaseModel):
    type: Literal[ActionType.WAIT]
    seconds: int = 1


class FailAction(BaseModel):
    type: Literal[ActionType.FAIL]
    message: str


Action = Union[
    KeyAction,
    ClickAction,
    RightClickAction,
    ScrollAction,
    TypeAction,
    DoubleClickAction,
    DragAction,
    MoveToAction,
    PressAction,
    HotkeyAction,
    MiddleClickAction,
    DoneAction,
    WaitAction,
    FailAction,
]


class Score(BaseModel):
    task_name: str
    score: float
    status: str
    success: bool
    steps_taken: int
    reward: float
    completion_reason: str
