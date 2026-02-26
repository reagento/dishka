from sqlite3 import Connection


class APIClient:
    ...


class DBGateway:
    def __init__(self, connection: Connection):
        ...


class Service:
    def __init__(self, client: APIClient, db: DBGateway):
        ...
