from . import Client as BaseClient

ID = "prover9"


class Client(BaseClient):
    _class_reasoner = ID


try:
    from . import AsyncClient as BaseAsyncClient

    class AsyncClient(BaseAsyncClient):
        _class_reasoner = ID
except ImportError:
    pass
