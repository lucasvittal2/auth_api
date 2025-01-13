import logging

from pymongo import MongoClient
from pymongo.errors import PyMongoError


class MongoHandler:
    def __init__(self, connection_string, database_name):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]

        except PyMongoError as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def get_document(self, collection_name: str, filter_query: dict) -> dict:
        """Retrieve a document matching the filter query."""
        try:
            collection = self.db[collection_name]
            document = collection.find_one(filter_query)
            return document
        except Exception as e:
            logging.error(
                f"Error retrieving document from '{collection_name}' collection: {e}"
            )
            return {}

    def create(self, collection_name: str, document) -> str:
        """Insert a new document into the specified collection."""
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            return result.inserted_id
        except Exception as e:
            logging.error(
                f"Error creating document in collection '{collection_name}': {e}"
            )
            return "ERROR"

    def upsert(
        self, collection_name: str, filter_query: dict, update_data: dict
    ) -> str:
        """Insert or update a document based on a filter query."""
        try:
            collection = self.db[collection_name]
            result = collection.update_one(
                filter_query, {"$set": update_data}, upsert=True
            )
            return result.upserted_id if result.upserted_id else "Updated"
        except Exception as e:
            logging.error(
                f"Error upserting document on '{collection_name}' collection: {e}"
            )
            return "ERROR"

    def delete(self, collection_name: str, filter_query) -> str:
        """Delete documents matching the filter query."""
        try:
            collection = self.db[collection_name]
            result = collection.delete_one(filter_query)
            return result.deleted_count
        except Exception as e:
            logging.error(f"Error deleting document: {e}")
            return "ERROR"


if __name__ == "__main__":
    # Setting up
    collection_name = "testing"
    handler = MongoHandler("mongodb://localhost:27017/", "test_db")

    # Testing
    handler.create(collection_name, {"name": "Test", "value": 123})
    doc = handler.get_document(collection_name, {"name": "Test"})
    print(doc)
    handler.upsert(collection_name, {"name": "Test"}, {"value": "456"})
    doc = handler.get_document(collection_name, {"name": "Test"})
    print(doc)
    handler.delete(collection_name, {"name": "Test"})
    doc = handler.get_document(collection_name, {"name": "Test"})
    print(doc)
