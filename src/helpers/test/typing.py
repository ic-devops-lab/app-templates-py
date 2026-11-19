from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from httpx2 import AsyncClient

type AsyncClientFactory = Callable[[], AbstractAsyncContextManager[AsyncClient]]
