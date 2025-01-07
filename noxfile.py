import sys
from collections.abc import Callable
from dataclasses import dataclass

import nox

PYTHON_3_13 = sys.version_info.minor == 13
CMD = ("pytest", "--cov=dishka", "--cov-append", "--cov-report=term-missing", "-v")
INSTALL_CMD = ("pytest", "pytest-cov", "-e", ".")


@dataclass(frozen=True, slots=True)
class IntegrationEnv:
    library: str
    version: str
    constraint: Callable[[], bool] = lambda: True

    def get_req(self) -> str:
        return f"requirements/{self.library.replace('_', '-')}-{self.version}.txt"

    def get_tests(self) -> str:
        return f"tests/integrations/{self.library}"


INTEGRATION_ENVS = [
    IntegrationEnv("aiogram", "330", lambda: not PYTHON_3_13),
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
    IntegrationEnv("faststream", "047", lambda: not PYTHON_3_13),
    IntegrationEnv("faststream", "050", lambda: not PYTHON_3_13),
    IntegrationEnv("faststream", "0529"),
    IntegrationEnv("faststream", "latest"),
    IntegrationEnv("flask", "302"),
    IntegrationEnv("flask", "latest"),
    IntegrationEnv("grpcio", "1641", lambda: not PYTHON_3_13),
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
]


for env in INTEGRATION_ENVS:
    @nox.session(
        reuse_venv=True,
        name=f"{env.library}_{env.version}",
        tags=[env.library, "latest" if env.version == "latest" else "non-latest"],
    )
    def session(session: nox.Session, env=env) -> None:
        if not env.constraint():
            session.skip("Skip tests on python 3.13 due to compatibility issues")
        session.install(*INSTALL_CMD, "-r", env.get_req())
        session.run(*CMD, env.get_tests())


@nox.session(reuse_venv=True)
def unit(session: nox.Session) -> None:
    session.install(
        *INSTALL_CMD,
        "-r", "requirements/test.txt",
    )
    session.run(*CMD, "tests/unit")


@nox.session(reuse_venv=True)
def real_world(session: nox.Session) -> None:
    session.install(
        *INSTALL_CMD,
        "-r", "examples/real_world/requirements_test.txt",
    )
    session.run(*CMD, "examples/real_world/tests/")


@nox.session(tags=["latest"])
def latest(session: nox.Session) -> None:
    for env in INTEGRATION_ENVS:
        if env.version == "latest":
            session.notify(f"{env.library}_{env.version}")


@nox.session(tags=["non-latest"], name="non-latest")
def not_latest(session: nox.Session) -> None:
    for env in INTEGRATION_ENVS:
        if env.version != "latest":
            session.notify(f"{env.library}_{env.version}")
