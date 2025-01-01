import sys

import nox

PYTHON_3_13 = sys.version_info.minor == 13
CMD = ("pytest", "--cov=dishka", "--cov-append", "--cov-report=term-missing", "-v")
PATH = {
    "aiogram_330": "requirements/aiogram-330.txt",
    "aiogram_3140": "requirements/aiogram-3140.txt",
    "aiogram_latest": "requirements/aiogram-latest.txt",
    "aiogram_dialog_210": "requirements/aiogram-dialog-210.txt",
    "aiogram_dialog_latest": "requirements/aiogram-dialog-latest.txt",
    "aiohttp_393": "requirements/aiohttp-393.txt",
    "aiohttp_latest": "requirements/aiohttp-latest.txt",
    "arq_0250": "requirements/arq-0250.txt",
    "arq_latest": "requirements/arq-latest.txt",
    "click_817": "requirements/click-817.txt",
    "click_latest": "requirements/click-latest.txt",
    "fastapi_0096": "requirements/fastapi-0096.txt",
    "fastapi_0109": "requirements/fastapi-0109.txt",
    "fastapi_latest": "requirements/fastapi-latest.txt",
    "faststream_047": "requirements/faststream-047.txt",
    "faststream_050": "requirements/faststream-050.txt",
    "faststream_0529": "requirements/faststream-0529.txt",
    "faststream_latest": "requirements/faststream-latest.txt",
    "flask_302": "requirements/flask-302.txt",
    "flask_latest": "requirements/flask-latest.txt",
    "grpcio_1641": "requirements/grpcio-1641.txt",
    "grpcio_1680": "requirements/grpcio-1680.txt",
    "grpcio_latest": "requirements/grpcio-latest.txt",
    "litestar_230": "requirements/litestar-230.txt",
    "litestar_latest": "requirements/litestar-latest.txt",
    "sanic_23121": "requirements/sanic-23121.txt",
    "sanic_latest": "requirements/sanic-latest.txt",
    "starlette_0270": "requirements/starlette-0270.txt",
    "starlette_latest": "requirements/starlette-latest.txt",
    "taskiq_0110": "requirements/taskiq-0110.txt",
    "taskiq_latest": "requirements/taskiq-latest.txt",
    "telebot_415": "requirements/telebot-415.txt",
    "telebot_latest": "requirements/telebot-latest.txt",
    "unit": "requirements/test.txt",
    "real_world_example": "examples/real_world/requirements_test.txt",
}


def install_requirements(session: nox.Session) -> None:
    session.install("pytest", "pytest-cov", "-e", ".")
    session.install("-r", PATH[session.name])


def run_tests(session: nox.Session, path: str) -> None:
    session.run(*CMD, path)


@nox.session(reuse_venv=True)
def aiogram_330(session: nox.Session) -> None:
    if PYTHON_3_13:
        session.skip("Skip tests on 3.13")
    install_requirements(session)
    run_tests(session, "tests/integrations/aiogram")


@nox.session(reuse_venv=True)
def aiogram_3140(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/aiogram")


@nox.session(reuse_venv=True)
def aiogram_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/aiogram")


@nox.session(reuse_venv=True)
def aiogram_dialog_210(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/aiogram_dialog")


@nox.session(reuse_venv=True)
def aiogram_dialog_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/aiogram_dialog")


@nox.session(reuse_venv=True)
def aiohttp_393(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/aiohttp")


@nox.session(reuse_venv=True)
def aiohttp_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/aiohttp")


@nox.session(reuse_venv=True)
def arq_0250(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/arq")


@nox.session(reuse_venv=True)
def arq_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/arq")


@nox.session(reuse_venv=True)
def click_817(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/click")


@nox.session(reuse_venv=True)
def click_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/click")


@nox.session(reuse_venv=True)
def fastapi_0096(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/fastapi")


@nox.session(reuse_venv=True)
def fastapi_0109(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/fastapi")


@nox.session(reuse_venv=True)
def fastapi_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/fastapi")


@nox.session(reuse_venv=True)
def faststream_047(session: nox.Session) -> None:
    if PYTHON_3_13:
        session.skip("Skip tests on 3.13")
    install_requirements(session)
    run_tests(session, "tests/integrations/faststream")


@nox.session(reuse_venv=True)
def faststream_050(session: nox.Session) -> None:
    if PYTHON_3_13:
        session.skip("Skip tests on 3.13")
    install_requirements(session)
    run_tests(session, "tests/integrations/faststream")


@nox.session(reuse_venv=True)
def faststream_0529(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/faststream")


@nox.session(reuse_venv=True)
def faststream_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/faststream")


@nox.session(reuse_venv=True)
def flask_302(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/flask")


@nox.session(reuse_venv=True)
def flask_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/flask")


@nox.session(reuse_venv=True)
def grpcio_1641(session: nox.Session) -> None:
    if PYTHON_3_13:
        session.skip("Skip tests on 3.13")
    install_requirements(session)
    run_tests(session, "tests/integrations/grpcio")


@nox.session(reuse_venv=True)
def grpcio_1680(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/grpcio")


@nox.session(reuse_venv=True)
def grpcio_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/grpcio")


@nox.session(reuse_venv=True)
def litestar_230(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/litestar")


@nox.session(reuse_venv=True)
def litestar_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/litestar")


@nox.session(reuse_venv=True)
def sanic_23121(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/sanic")


@nox.session(reuse_venv=True)
def sanic_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/sanic")


@nox.session(reuse_venv=True)
def starlette_0270(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/starlette")


@nox.session(reuse_venv=True)
def starlette_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/starlette")


@nox.session(reuse_venv=True)
def taskiq_0110(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/taskiq")


@nox.session(reuse_venv=True)
def taskiq_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/taskiq")


@nox.session(reuse_venv=True)
def telebot_415(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/telebot")


@nox.session(reuse_venv=True)
def telebot_latest(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/integrations/telebot")


@nox.session(reuse_venv=True)
def unit(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "tests/unit")


@nox.session(reuse_venv=True)
def real_world_example(session: nox.Session) -> None:
    install_requirements(session)
    run_tests(session, "examples/real_world/tests/")
