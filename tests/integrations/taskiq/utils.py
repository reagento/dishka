import pickle

from taskiq import AsyncResultBackend, TaskiqResult


class PickleResultBackend(AsyncResultBackend):
    def __init__(self) -> None:
        self.results = {}

    async def set_result(self, task_id, result) -> None:
        self.results[task_id] = pickle.dumps(result)

    async def is_result_ready(self, task_id) -> bool:
        return task_id in self.results

    async def get_result(
        self,
        task_id: str,
        with_logs: bool = False,  # noqa: FBT001, FBT002
    ) -> TaskiqResult:
        return pickle.loads(self.results[task_id])  # noqa: S301
