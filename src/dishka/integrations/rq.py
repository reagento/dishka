from collections.abc import Callable
from inspect import signature
from typing import Any, get_type_hints

from rq import Queue, Worker
from rq.job import Job

from dishka import Container
from dishka.integrations.base import default_parse_dependency


class DishkaWorker(Worker):
    """Custom RQ Worker class with Dishka DI support."""

    def __init__(
        self,
        *args,
        container: Container,
        **kwargs,
    ) -> None:
        """Sets up class and container."""
        super().__init__(*args, **kwargs)
        self.dishka_container = container

    def perform_job(self, job: Job, queue: Queue) -> bool:
        """Performs job call"""
        request_container = self.dishka_container().__enter__()
        self.inject_deps(job, request_container)
        job_result = super().perform_job(job, queue)
        request_container.close()
        return job_result

    def inject_deps(self, job: Job, container: Container) -> None:
        """Injects dependencies into using the Dishka container.

        Args:
            job: The RQ job to inject dependencies into.
        """
        if job.func:
            dependencies = self._build_dependencies(job.func)
            updated_kwargs = self._build_kwargs(dependencies, container)
            if isinstance(job.kwargs, dict):
                job.kwargs.update(updated_kwargs)

    def teardown(self) -> None:
        """Closes DI container on worker shutdown."""
        self.dishka_container.close()
        super().teardown()

    @classmethod
    def _build_dependencies(
        cls, callable_: Callable[..., Any],
    ) -> dict[str, Any]:
        """Builds dependencies for the given callable."""
        dependencies = {}

        for name, parameter in signature(callable_).parameters.items():
            dep = default_parse_dependency(
                parameter,
                get_type_hints(callable_, include_extras=True).get(name, Any),
            )
            if dep is None:
                continue
            dependencies[name] = dep

        return dependencies

    def _build_kwargs(
        self,
        dependencies: dict,
        request_container: Container,
    ) -> dict[str, Any]:
        """Buld kwargs dict for RQ job run."""
        return {
            name: request_container.get(dep.type_hint, component=dep.component)
            for name, dep in dependencies.items()
        }
