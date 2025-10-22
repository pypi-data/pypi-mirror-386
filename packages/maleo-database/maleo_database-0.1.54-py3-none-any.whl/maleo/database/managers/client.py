from elasticsearch import AsyncElasticsearch, Elasticsearch
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from redis.asyncio import Redis as AsyncRedis
from redis import Redis as SyncRedis
from typing import Generic, Literal, Tuple, TypeVar, overload
from maleo.types.string import ListOfStrs
from ..config import (
    ElasticsearchConfig,
    MongoConfig,
    RedisConfig,
    NoSQLConfigT,
)
from ..enums import Connection


AsyncClientT = TypeVar(
    "AsyncClientT", AsyncElasticsearch, AsyncIOMotorClient, AsyncRedis
)


SyncClientT = TypeVar("SyncClientT", Elasticsearch, MongoClient, SyncRedis)


class ClientManager(
    Generic[
        NoSQLConfigT,
        AsyncClientT,
        SyncClientT,
    ]
):
    def __init__(self, config: NoSQLConfigT) -> None:
        super().__init__()
        self._config = config

        self._async_client = self._config.create_client(Connection.ASYNC)
        self._sync_client = self._config.create_client(Connection.SYNC)

    @overload
    def get(self, connection: Literal[Connection.ASYNC]) -> AsyncClientT: ...
    @overload
    def get(self, connection: Literal[Connection.SYNC]) -> SyncClientT: ...
    def get(
        self, connection: Connection = Connection.ASYNC
    ) -> AsyncClientT | SyncClientT:
        if connection is Connection.ASYNC:
            return self._async_client
        elif connection is Connection.SYNC:
            return self._sync_client

    def get_all(self) -> Tuple[AsyncClientT, SyncClientT]:
        return (self._async_client, self._sync_client)

    async def dispose(self):
        if isinstance(self._async_client, AsyncIOMotorClient):
            self._async_client.close()
        else:
            await self._async_client.close()
        self._sync_client.close()


class ElasticsearchClientManager(
    ClientManager[ElasticsearchConfig, AsyncElasticsearch, Elasticsearch]
):
    pass


class MongoClientManager(ClientManager[MongoConfig, AsyncIOMotorClient, MongoClient]):
    pass


class RedisClientManager(ClientManager[RedisConfig, AsyncRedis, SyncRedis]):
    async def async_clear(self, prefixes: ListOfStrs | str | None = None):
        if prefixes is None:
            prefixes = [self._config.additional.base_namespace]

        if isinstance(prefixes, str):
            prefixes = [prefixes]

        for prefix in prefixes:
            async for key in self._async_client.scan_iter(f"{prefix}*"):
                await self._async_client.delete(key)

    def sync_clear(self, prefixes: ListOfStrs | str | None = None):
        if prefixes is None:
            prefixes = [self._config.additional.base_namespace]

        if isinstance(prefixes, str):
            prefixes = [prefixes]

        for prefix in prefixes:
            for key in self._sync_client.scan_iter(f"{prefix}*"):
                self._sync_client.delete(key)


ClientManagerT = TypeVar(
    "ClientManagerT",
    ElasticsearchClientManager,
    MongoClientManager,
    RedisClientManager,
)
