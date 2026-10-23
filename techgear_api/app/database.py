from collections.abc import AsyncIterator

from fastapi import Request
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import settings


def create_mongo_client() -> AsyncMongoClient:
    return AsyncMongoClient(settings.mongodb_url)


async def get_database(request: Request) -> AsyncIterator[AsyncDatabase]:
    yield request.app.state.database
