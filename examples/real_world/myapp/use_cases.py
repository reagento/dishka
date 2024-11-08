from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol


class User:
    pass


@dataclass
class Product:
    owner_id: int
    name: str


class UserNotFoundError(Exception):
    pass


class UserGateway(Protocol):
    @abstractmethod
    def get_user(self, user_id: int) -> User:
        raise NotImplementedError


class ProductGateway(Protocol):
    @abstractmethod
    def add_product(self, product: Product) -> None:
        raise NotImplementedError


class Commiter(Protocol):
    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError


class WarehouseClient(Protocol):
    @abstractmethod
    def next_product(self) -> str:
        raise NotImplementedError


class AddProductsInteractor:
    def __init__(
            self,
            user_gateway: UserGateway,
            product_gateway: ProductGateway,
            commiter: Commiter,
            warehouse_client: WarehouseClient,
    ) -> None:
        self.user_gateway = user_gateway
        self.product_gateway = product_gateway
        self.commiter = commiter
        self.warehouse_client = warehouse_client

    def __call__(self, user_id: int):
        user = self.user_gateway.get_user(user_id)
        if user is None:
            raise UserNotFoundError

        product = Product(user_id, self.warehouse_client.next_product())
        self.product_gateway.add_product(product)
        product2 = Product(user_id, self.warehouse_client.next_product())
        self.product_gateway.add_product(product2)
        self.commiter.commit()
