import logging

from .use_cases import WarehouseClient

logger = logging.getLogger(__name__)


class FakeWarehouseClient(WarehouseClient):
    def __init__(self):
        logger.info("init FakeWarehouseClient as %s", self)
        self.products = 0

    def next_product(self) -> str:
        self.products += 1
        return f"Product {self.products}"
