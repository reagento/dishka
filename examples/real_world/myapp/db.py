import logging

from .use_cases import ProductGateway, Commiter, User, UserGateway, Product

logger = logging.getLogger(__name__)


class FakeCommiter(Commiter):
    def __init__(self):
        logger.info("init FakeCommiter as %s", self)

    def commit(self) -> None:
        logger.info("commit as %s", self)

    def close(self) -> None:
        logger.info("close as %s", self)


class FakeUserGateway(UserGateway):
    def __init__(self, commiter: FakeCommiter):
        self.commiter = commiter
        logger.info("init FakeUserGateway with %s", commiter)

    def get_user(self, user_id: int) -> User:
        logger.info("get_user %s as %s", user_id, self)
        return User()


class FakeProductGateway(ProductGateway):
    def __init__(self, commiter: FakeCommiter):
        self.commiter = commiter
        logger.info("init FakeProductGateway with %s", commiter)

    def add_product(self, product: Product) -> None:
        logger.info(
            "add_product %s for user %s, by %s",
            product.name, product.owner_id, self,
        )
