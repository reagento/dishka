from enum import Enum


class BaseScope(Enum):
    pass


class Scope(BaseScope):
    APP = "APP"
    REQUEST = "REQUEST"
    ACTION = "ACTION"
    STEP = "STEP"
