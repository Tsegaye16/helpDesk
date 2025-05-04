import chromadb
import uuid
from typing import List, Dict
import logging
from chromadb.config import Settings

from config import CHROMA_PERSIST_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """Manages chat history storage and retrieval using ChromaDB."""
    
    def __init__(self, persist_directory: str = CHROMA_PERSIST_DIR):
        """Initialize ChromaDB client."""
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self._get_or_create_collection()
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {e}")
            raise

    def _get_or_create_collection(self):
        """Get or create a ChromaDB collection for chat history."""
        collection_name = "chat_history"
        try:
            # Check if collection exists
            collections = self.client.list_collections()
            if any(c.name == collection_name for c in collections):
                return self.client.get_collection(collection_name)
            return self.client.create_collection(collection_name)
        except Exception as e:
            logger.error(f"Error getting or creating collection: {e}")
            raise

    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())

    def save_chat_message(self, session_id: str, role: str, content: str) -> None:
        """Save a chat message to ChromaDB."""
        try:
            message_id = str(uuid.uuid4())
            self.collection.add(
                documents=[content],
                metadatas=[{"session_id": session_id, "role": role}],
                ids=[message_id]
            )
            logger.info(f"Saved chat message for session {session_id}")
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            raise

    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve chat history for a given session ID."""
        try:
            results = self.collection.query(
                query_texts=[""],  # Empty query to get all documents
                where={"session_id": session_id},
                n_results=1000  # Adjust based on expected history size
            )
            history = [
                {"role": metadata["role"], "content": doc}
                for doc, metadata in zip(results["documents"][0], results["metadatas"][0])
            ]
            logger.info(f"Retrieved {len(history)} messages for session {session_id}")
            return history
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []