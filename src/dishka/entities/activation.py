from typing import Protocol


class Marker:
    def __init__(self, value: str):
        self.value = value

    # TODO: ~, |, &
