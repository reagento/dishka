import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from itertools import chain
from typing import Protocol

import nox

nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True

CMD = (
    "pytest",
    "--cov=dishka",
    "--cov-append",
    "--cov-report=term-missing",
    "-v",
)
INSTALL_CMD = ("pytest", "pytest-cov", "-e", ".")


@dataclass(frozen=True, slots=True)
class Constraint:
    reason: str = ""
    condition: Callable[[], bool] = lambda: True


@dataclass(frozen=True, slots=True)
class Requirement:
    req: str
    tests: str


class NoxEnvironment(Protocol):
    constraint: Constraint | None

    @property
    def requirements(self) -> Iterable[Requirement]: ...

    @property
    def name(self) -> str: ...

    @property
    def tags(self) -> list[str]: ...


@dataclass(frozen=True, slots=True)
class IntegrationEnv(NoxEnvironment):
    library: str
    version: str
    constraint: Constraint | None = None

    @property
    def requirements(self) -> Iterable[Requirement]:
        return (
            Requirement(
                req=(
                    "requirements/"
                    f"{self.library.replace('_', '-')}"
                    f"-{self.version}.txt"
                ),
                tests=f"tests/integrations/{self.library}",
            ),
        )

    @property
    def name(self) -> str:
        return f"{self.library}_{self.version}"

    @property
    def tags(self) -> list[str]:
        return [self.library, "latest" if self.version == "latest" else "ci"]


@dataclass(frozen=True, slots=True)
class IntegrationAlias(NoxEnvironment):
    library: str
    integrations: list[IntegrationEnv]
    constraint: Constraint | None = None

    @property
    def requirements(self) -> Iterable[Requirement]:
        return chain(
            req
            for integration in self.integrations
            for req in integration.requirements
        )

    @property
    def name(self) -> str:
        return self.library

    @property
    def tags(self) -> list[str]:
        return [self.library]


constraint_3_13 = Constraint(
    "Skip tests on python 3.13 due to compatibility issues",
    lambda: sys.version_info < (3, 13),
)

INTEGRATIONS = [
    IntegrationEnv("aiogram", "330", constraint_3_13),
    IntegrationEnv("aiogram", "3140"),
    IntegrationEnv("aiogram", "latest"),
    IntegrationEnv("aiogram_dialog", "210"),
    IntegrationEnv("aiogram_dialog", "latest"),
    IntegrationEnv("aiohttp", "393"),
    IntegrationEnv("aiohttp", "latest"),
    IntegrationEnv("arq", "0250"),
    IntegrationEnv("arq", "latest"),
    IntegrationEnv("click", "817"),
    IntegrationEnv("click", "latest"),
    IntegrationEnv("fastapi", "0096"),
    IntegrationEnv("fastapi", "0109"),
    IntegrationEnv("fastapi", "latest"),
    IntegrationAlias(
        "faststream",
        integrations=[
            IntegrationEnv("faststream", "047", constraint_3_13),
            IntegrationEnv("faststream", "050", constraint_3_13),
            IntegrationEnv("faststream", "0529"),
            IntegrationEnv("faststream", "latest"),
        ],
    ),
    IntegrationEnv("flask", "302"),
    IntegrationEnv("flask", "latest"),
    IntegrationEnv("grpcio", "1641", constraint_3_13),
    IntegrationEnv("grpcio", "1680"),
    IntegrationEnv("grpcio", "latest"),
    IntegrationEnv("litestar", "230"),
    IntegrationEnv("litestar", "latest"),
    IntegrationEnv("sanic", "23121"),
    IntegrationEnv("sanic", "latest"),
    IntegrationEnv("starlette", "0270"),
    IntegrationEnv("starlette", "latest"),
    IntegrationEnv("taskiq", "0110"),
    IntegrationEnv("taskiq", "latest"),
    IntegrationEnv("telebot", "415"),
    IntegrationEnv("telebot", "latest"),
    IntegrationEnv("celery", "540"),
    IntegrationEnv("celery", "latest"),
]


@nox.session(tags=["ci"])
def integrations_base(session: nox.Session) -> None:
    session.install(
        *INSTALL_CMD,
        "-r",
        "requirements/test.txt",
    )
    session.run(*CMD, "tests/integrations/base")


def register_env(env: NoxEnvironment) -> None:
    @nox.session(name=env.name, tags=env.tags)
    def session(session: nox.Session, env: NoxEnvironment = env) -> None:
        if env.constraint and not env.constraint.condition():
            session.skip(env.constraint.reason)

        for req in env.requirements:
            session.install(*INSTALL_CMD, "-r", req.req)
            session.run(*CMD, req.tests)


for env in INTEGRATIONS:
    if isinstance(env, IntegrationAlias):
        register_env(env)

        for e in env.integrations:
            register_env(e)

    else:
        register_env(env)


@nox.session(tags=["ci"])
def unit(session: nox.Session) -> None:
    session.install(
        *INSTALL_CMD,
        "-r",
        "requirements/test.txt",
    )
    session.run(*CMD, "tests/unit")


@nox.session(tags=["ci"])
def real_world(session: nox.Session) -> None:
    session.install(
        *INSTALL_CMD,
        "-r",
        "examples/real_world/requirements_test.txt",
    )
    session.run(*CMD, "examples/real_world/tests/")
