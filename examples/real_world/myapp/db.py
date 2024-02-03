import logging

from .use_cases import ProductGateway, UnitOfWork, User, UserGateway

logger = logging.getLogger(__name__)


class FakeDbConnection(UnitOfWork):
    def __init__(self):
        logger.info("init FakeDbConnection as %s", self)

    def commit(self) -> None:
        logger.info("commit as %s", self)

    def close(self) -> None:
        logger.info("close as %s", self)


class FakeUserGateway(UserGateway):
    def __init__(self, unit_of_work: FakeDbConnection):
        self.unit_of_work = unit_of_work
        logger.info("init FakeUserGateway with %s", unit_of_work)

    def get_user(self, user_id: int) -> User:
        logger.info("get_user %s as %s", user_id, self)
        return User()


class FakeProductGateway(ProductGateway):
    def __init__(self, unit_of_work: FakeDbConnection):
        self.unit_of_work = unit_of_work
        logger.info("init FakeProductGateway with %s", unit_of_work)

    def add_product(self, user_id: int, product: str) -> None:
        logger.info("add_product %s for user %s, by %s", product, user_id,
                    self)

