from pinecone import Pinecone
from app.config import (
    PINECONE_API_KEY,
    PINECONE_INDEX,
    PINECONE_NAMESPACE,
    MONGODB_COLLECTION_NAME,
    MONGODB_URI,
    MONGODB_DB_NAME,
)
import pymongo

from dataclasses import dataclass


@dataclass(frozen=True)
class PineconeIdx1536_Namespaces:
    """Dataclass to store the namespaces for the pinecone index."""

    doc_rag: str = PINECONE_NAMESPACE
    intent_classifier = "intent_classifier"


_pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = _pc.Index(PINECONE_INDEX)

_mongo_client = pymongo.MongoClient(MONGODB_URI)
_db = _mongo_client[MONGODB_DB_NAME]
structured_data_collection = _db[MONGODB_COLLECTION_NAME]
