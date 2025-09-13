import sys
from collections.abc import Callable
from dataclasses import dataclass

import nox

nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True

INSTALL_CMD = ("pytest", "pytest-cov", "-e", ".")


@dataclass(frozen=True, slots=True)
class Constraint:
    reason: str = ""
    condition: Callable[[], bool] = lambda: True


@dataclass(frozen=True, slots=True)
class IntegrationEnv:
    library: str
    version: str
    constraint: Constraint | None = None

    def get_req(self) -> str:
        return f"requirements/{self.library.replace('_', '-')}-{self.version}.txt"

    def get_tests(self) -> str:
        return f"tests/integrations/{self.library}"


def python_version_less(*version: int) -> Constraint:
    version_str = ".".join(map(str, version))
    return Constraint(
        f"Skip tests on python {version_str} due to compatibility issues",
        lambda: sys.version_info < version,
    )


INTEGRATIONS = [
    IntegrationEnv("aiogram", "330", python_version_less(3, 13)),
    IntegrationEnv("aiogram", "3140", python_version_less(3, 14)),
    IntegrationEnv("aiogram", "latest"),
    IntegrationEnv("aiogram_dialog", "210", python_version_less(3, 14)),
    IntegrationEnv("aiogram_dialog", "latest"),
    IntegrationEnv("aiohttp", "393", python_version_less(3, 14)),
    IntegrationEnv("aiohttp", "31215"),
    IntegrationEnv("aiohttp", "latest"),
    IntegrationEnv("arq", "0250"),
    IntegrationEnv("arq", "latest"),
    IntegrationEnv("click", "817"),
    IntegrationEnv("click", "latest"),
    IntegrationEnv("fastapi", "0096", python_version_less(3, 14)),
    IntegrationEnv("fastapi", "0109"),
    IntegrationEnv("fastapi", "latest"),
    IntegrationEnv("faststream", "050", python_version_less(3, 13)),
    IntegrationEnv("faststream", "0529", python_version_less(3, 14)),
    IntegrationEnv("faststream", "060"),
    IntegrationEnv("faststream", "latest"),
    IntegrationEnv("flask", "302"),
    IntegrationEnv("flask", "latest"),
    IntegrationEnv("grpcio", "1641", python_version_less(3, 13)),
    IntegrationEnv("grpcio", "1680", python_version_less(3, 14)),
    IntegrationEnv("grpcio", "latest"),
    IntegrationEnv("litestar", "232"),
    IntegrationEnv("litestar", "latest"),
    IntegrationEnv("sanic", "23121", python_version_less(3, 14)),
    IntegrationEnv("sanic", "2530"),
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
        "-r", "requirements/test.txt",
        silent=False,
    )
    session.run("pytest", "tests/integrations/base")


for env in INTEGRATIONS:
    @nox.session(
        name=f"{env.library}_{env.version}",
        tags=[env.library, "latest" if env.version == "latest" else "ci"],
    )
    def session(session: nox.Session, env=env) -> None:
        if env.constraint and not env.constraint.condition():
            session.skip(env.constraint.reason)

        session.install(*INSTALL_CMD, "-r", env.get_req(), silent=False)
        session.run("pytest", env.get_tests())


@nox.session(tags=["ci"])
def unit(session: nox.Session) -> None:
    session.install(
        *INSTALL_CMD,
        "-r", "requirements/test.txt",
        silent=False,
    )
    session.run("pytest", "tests/unit")


@nox.session(tags=["ci"])
def real_world(session: nox.Session) -> None:
    if sys.version_info >= (3, 14):
        session.skip("Skipping tests on python >=3.14 due to requirements limitations")
    session.install(
        *INSTALL_CMD,
        "-r", "examples/real_world/requirements_test.txt",
        silent=False,
    )
    session.run("pytest", "examples/real_world/tests/")
