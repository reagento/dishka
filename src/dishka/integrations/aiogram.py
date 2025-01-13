__all__ = [
    "CONTAINER_NAME",
    "AiogramMiddlewareData",
    "AiogramProvider",
    "AutoInjectMiddleware",
    "FromDishka",
    "inject",
    "inject_handler",
    "inject_router",
    "setup_dishka",
]

import warnings
from collections.abc import Awaitable, Callable, Container
from dataclasses import asdict, dataclass
from functools import partial
from inspect import Parameter, signature
from typing import Any, Final, ParamSpec, TypeVar, cast

from aiogram import BaseMiddleware, Bot, Dispatcher, Router
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import Chat, TelegramObject, User

from dishka import AsyncContainer, FromDishka, Provider, Scope, from_context
from .base import is_dishka_injected, wrap_injection

try:
    from aiogram.dispatcher.middlewares.user_context import EventContext
    IS_AIOGRAM_HAS_EVENT_CONTEXT = True
except ImportError:
    IS_AIOGRAM_HAS_EVENT_CONTEXT = False


P = ParamSpec("P")
T = TypeVar("T")
CONTAINER_NAME: Final = "dishka_container"


def inject(func: Callable[P, T]) -> Callable[P, T]:
    if CONTAINER_NAME in signature(func).parameters:
        additional_params = []
    else:
        additional_params = [Parameter(
            name=CONTAINER_NAME,
            annotation=Container,
            kind=Parameter.KEYWORD_ONLY,
        )]

    return wrap_injection(
        func=func,
        is_async=True,
        additional_params=additional_params,
        container_getter=lambda args, kwargs: kwargs[CONTAINER_NAME],
    )


# dont import from aiogram because its not available unitl v3.5.0
@dataclass(frozen=True)
class EventContext:
    chat: Chat | None = None
    user: User | None = None
    thread_id: int | None = None
    business_connection_id: str | None = None

    @property
    def user_id(self) -> int | None:
        return self.user.id if self.user else None

    @property
    def chat_id(self) -> int | None:
        return self.chat.id if self.chat else None


@dataclass
class AiogramMiddlewareData:
    event: TelegramObject
    bot: Bot
    bots: list[Bot] | None  # with polling
    dispatcher: Dispatcher  # with polling
    event_context: EventContext
    fsm_storage: BaseStorage | None  # with fsm
    state: FSMContext | None  # with fsm and event.from_user is not None
    raw_state: str | None  # with fsm
    data: dict[str, Any]


class AiogramProvider(Provider):
    event = from_context(TelegramObject, scope=Scope.REQUEST)
    middleware_data = from_context(AiogramMiddlewareData, scope=Scope.REQUEST)


class ContainerMiddleware(BaseMiddleware):
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        event_context = self._resolve_event_context(data)
        middleware_data = self._get_middleware_data(event, event_context, data)

        async with self.container(
                {
                    TelegramObject: event,
                    AiogramMiddlewareData: middleware_data,
                },
        ) as sub_container:
            data[CONTAINER_NAME] = sub_container
            return await handler(event, data)

    def _resolve_event_context(self, data: dict[str, Any]) -> EventContext:
        if IS_AIOGRAM_HAS_EVENT_CONTEXT:
            return EventContext(**asdict(data["event_context"]))

        chat: Chat | None = data.get("event_chat")
        user: User | None = data.get("event_from_user")
        thread_id: int | None = data.get("event_thread_id")
        return EventContext(chat=chat, user=user, thread_id=thread_id)

    def _get_middleware_data(
            self,
            event: TelegramObject,
            event_context: EventContext,
            data: dict[str, Any],
    ) -> AiogramMiddlewareData:
        return AiogramMiddlewareData(
            event=event,
            bot=data["bot"],
            bots=data.get("bots"),
            dispatcher=data.get("dispatcher"),
            event_context=event_context,
            fsm_storage=data.get("fsm_storage"),
            state=data.get("state"),
            raw_state=data.get("raw_state"),
            data=data,
        )


class AutoInjectMiddleware(BaseMiddleware):
    def __init__(self):
        warnings.warn(
            f"{self.__class__.__name__} is slow, "
            "use `setup_dishka` instead if you care about performance",
            UserWarning,
            stacklevel=2,
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        old_handler = cast(HandlerObject, data["handler"])
        if is_dishka_injected(old_handler.callback):
            return await handler(event, data)

        inject_handler(old_handler)
        return await handler(event, data)


def setup_dishka(
    container: AsyncContainer,
    router: Router,
    *,
    auto_inject: bool = False,
) -> None:
    middleware = ContainerMiddleware(container)

    for observer in router.observers.values():
        observer.outer_middleware(middleware)

    if auto_inject:
        callback = partial(inject_router, router=router)
        router.startup.register(callback)


def inject_router(router: Router) -> None:
    """Inject dishka to the router handlers."""
    for observer in router.observers.values():
        if observer.event_name == "update":
            continue

        for handler in observer.handlers:
            if not is_dishka_injected(handler.callback):
                inject_handler(handler)


def inject_handler(handler: HandlerObject) -> HandlerObject:
    """Inject dishka for callback in aiogram's handler."""
    # temp_handler is used to apply original __post_init__ processing
    # for callback object wrapped by injector
    temp_handler = HandlerObject(
        callback=inject(handler.callback),
        filters=handler.filters,
        flags=handler.flags,
    )

    # since injector modified callback and params,
    # we should update them in the original handler
    handler.callback = temp_handler.callback
    handler.params = temp_handler.params

    return handler
