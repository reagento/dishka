from enum import Enum


class BaseScope(Enum):
    pass


class Scope(BaseScope):
    APP = "APP"
    REQUEST = "REQUEST"
    ACTION = "ACTION"
    STEP = "STEP"


class InvalidScopes(BaseScope):
    UNKNOWN_SCOPE = "<unknown scope>"

    def __str__(self):
        return self.value
