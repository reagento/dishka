import sys
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import nox

nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True

INSTALL_CMD = ("pytest", "pytest-cov", "-e", ".", "-r")


@dataclass(frozen=True, slots=True)
class Constraint:
    reason: str = ""
    condition: Callable[[], bool] = lambda: True


@dataclass(frozen=True, slots=True)
class IntegrationEnv:
    library: str
    version: str
    constraint: Constraint | None = None

    def get_req(self) -> tuple[str, str]:
        return f"requirements/{self.library}.toml", self.version

    def get_tests(self) -> str:
        return f"tests/integrations/{self.library}"


def skip_major_version(version: tuple[int, int]) -> Constraint:
    return Constraint(
        f"Skip tests on python {version[0]}.{version[1]} due to compatibility issues",
        lambda: sys.version_info < version,
    )


INTEGRATIONS = [
    IntegrationEnv("aiogram", "330", skip_major_version((3, 13))),
    IntegrationEnv("aiogram", "3140", skip_major_version((3, 13))),
    IntegrationEnv("aiogram", "latest"),
    IntegrationEnv("aiogram_dialog", "210", skip_major_version((3, 14))),
    IntegrationEnv("aiogram_dialog", "latest"),
    IntegrationEnv("aiohttp", "393", skip_major_version((3, 14))),
    IntegrationEnv("aiohttp", "31215"),
    IntegrationEnv("aiohttp", "latest"),
    IntegrationEnv("arq", "0250"),
    IntegrationEnv("arq", "latest"),
    IntegrationEnv("click", "817"),
    IntegrationEnv("click", "latest"),
    IntegrationEnv("fastapi", "0096"),
    IntegrationEnv("fastapi", "0109"),
    IntegrationEnv("fastapi", "latest"),
    IntegrationEnv("faststream", "047", skip_major_version((3, 13))),
    IntegrationEnv("faststream", "050", skip_major_version((3, 13))),
    IntegrationEnv("faststream", "0529"),
    IntegrationEnv("faststream", "latest"),
    IntegrationEnv("flask", "302"),
    IntegrationEnv("flask", "latest"),
    IntegrationEnv("grpcio", "1641", skip_major_version((3, 13))),
    IntegrationEnv("grpcio", "1680"),
    IntegrationEnv("grpcio", "latest"),
    IntegrationEnv("litestar", "232"),
    IntegrationEnv("litestar", "latest"),
    IntegrationEnv("sanic", "23121", skip_major_version((3, 14))),
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
        "requirements/test.txt",
        silent=False,
    )
    session.run("pytest", "tests/integrations/base")


def load_toml(toml: str, group: str) -> list[str]:
    data = tomllib.loads(Path(toml).read_text(encoding="utf-8"))
    return data["versions"][group]


for env in INTEGRATIONS:
    @nox.session(
        name=f"{env.library}_{env.version}",
        tags=[env.library, "latest" if env.version == "latest" else "ci"],
    )
    def session(session: nox.Session, env=env) -> None:
        if env.constraint and not env.constraint.condition():
            session.skip(env.constraint.reason)

        session.install(
            *INSTALL_CMD,
            "requirements/test.txt",
            *load_toml(*env.get_req()),
            silent=False,
        )
        session.run("pytest", env.get_tests())


@nox.session(tags=["ci"])
def unit(session: nox.Session) -> None:
    session.install(
        *INSTALL_CMD,
        "requirements/test.txt",
        silent=False,
    )
    session.run("pytest", "tests/unit")


@nox.session(tags=["ci"])
def real_world(session: nox.Session) -> None:
    session.install(
        *INSTALL_CMD,
        "examples/real_world/requirements_test.txt",
        silent=False,
    )
    session.run("pytest", "examples/real_world/tests/")
