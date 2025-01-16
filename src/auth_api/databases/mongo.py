import logging

from pymongo import MongoClient
from pymongo.errors import PyMongoError


class MongoHandler:
    def __init__(self, connection_string, database_name):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]
            logging.info(f"Connected to mongoDB on {database_name} database.")
        except PyMongoError as err:
            logging.error(f"Failed to connect to MongoDB: {err}")
            raise err

    def get_document(self, collection_name: str, filter_query: dict) -> dict:
        """Retrieve a document matching the filter query."""
        try:
            logging.info("getting a document...")
            collection = self.db[collection_name]
            document = collection.find_one(filter_query)
            logging.info("Got the document.")
            return document
        except Exception as err:
            logging.error(
                f"Error retrieving document from '{collection_name}' collection: {err}"
            )
            raise err

    def create(self, collection_name: str, document) -> str:
        """Insert a new document into the specified collection."""
        try:
            logging.info(f"creating collection {collection_name}")
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            logging.info(f"created collection {collection_name}")
            return result.inserted_id
        except Exception as err:
            logging.error(
                f"Error creating document in collection '{collection_name}': {err}"
            )
            raise err

    def upsert(
        self, collection_name: str, filter_query: dict, update_data: dict
    ) -> str:
        """Insert or update a document based on a filter query."""
        try:
            logging.info("upserting a document...")
            collection = self.db[collection_name]
            result = collection.update_one(
                filter_query, {"$set": update_data}, upsert=True
            )
            logging.info("Upserted a document.")
            return result.upserted_id if result.upserted_id else "Updated"
        except Exception as err:
            logging.error(
                f"Error upserting document on '{collection_name}' collection: {err}"
            )
            raise err

    def delete(self, collection_name: str, filter_query) -> None:
        """Delete documents matching the filter query."""
        try:
            collection = self.db[collection_name]
            collection.delete_one(filter_query)
        except Exception as err:
            logging.error(f"Error deleting document: {err}")
            raise err

    def create_collection_if_not_exist(self, collection_name: str) -> None:
        try:
            collections = [el["name"] for el in self.db.list_collections().to_list()]
            if collection_name not in collections:
                self.db.create_collection(collection_name)
                logging.info(f"created collection '{collection_name}' !")
            else:
                logging.info(
                    f"Collection '{collection_name}' already exists, not necessary create it again."
                )

        except Exception as err:
            logging.error(f"Error deleting document: {err}")
            raise err


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
