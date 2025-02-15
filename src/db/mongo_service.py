from typing import List
from pymongo.collection import Collection
from pymongo.errors import OperationFailure
from loguru import logger

from src.scraper_entities import ProcessedPost
from src.settings import settings
from src.db.mongo_connect import connection


class MongoDBService:
    """Handles MongoDB CRUD operations"""

    def __init__(self) -> None:
        self.client = connection
        self.database = self.client.get_database(settings.MONGO_DB_NAME)
        self.collection = self.database[settings.MONGO_COLLECTION]

    def get_documents_bulk(self, **filter_options) -> List[ProcessedPost]:
        try:
            instances = self.collection.find(filter_options, {"_id": 0})
            return [ProcessedPost(**post) for post in instances]

        except OperationFailure:
            logger.error("Failed to retrieve documents.")

            return []
