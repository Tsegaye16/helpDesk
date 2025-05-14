import chromadb
import uuid
from typing import List, Dict
import logging
from datetime import datetime
from config import CHROMA_PERSIST_DIR
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatHistoryManager:
    def __init__(self, persist_directory: str = CHROMA_PERSIST_DIR):
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=chromadb.config.Settings(anonymized_telemetry=False)
            )
            self.collection = self._get_or_create_collection()
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {e}")
            raise

    def _get_or_create_collection(self):
        collection_name = "chat_history"
        try:
            collections = self.client.list_collections()
            if any(c.name == collection_name for c in collections):
                return self.client.get_collection(collection_name)
            return self.client.create_collection(collection_name)
        except Exception as e:
            logger.error(f"Error getting or creating collection: {e}")
            raise

    def generate_session_id(self) -> str:
        return str(uuid.uuid4())

    def save_chat_message(self, session_id: str, role: str, content: str) -> None:
        try:
            message_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            self.collection.add(
                documents=[content],
                metadatas=[{
                    "session_id": session_id,
                    "role": role,
                    "timestamp": timestamp,
                    "type": "message"
                }],
                ids=[message_id]
            )
            logger.info(f"Saved chat message for session {session_id}")
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            raise

    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        try:
            results = self.collection.query(
                query_texts=[""],
                where={
                    "$and": [
                        {"session_id": {"$eq": session_id}},
                        {"type": {"$eq": "message"}}
                    ]
                },
                n_results=1000
            )
            messages = []
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                # Skip if metadata is missing required fields
                if not all(key in metadata for key in ["role", "timestamp"]):
                    logger.warning(f"Skipping invalid chat history document: {metadata}")
                    continue
                messages.append({
                    "role": metadata["role"],
                    "content": doc,
                    "timestamp": metadata["timestamp"]
                })
            sorted_messages = sorted(messages, key=lambda x: x["timestamp"])
            history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in sorted_messages
            ]
            logger.info(f"Retrieved {len(history)} messages for session {session_id}")
            return history
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []

    def save_session_state(self, session_id: str, state: Dict) -> None:
        try:
            state_id = f"state_{session_id}"
            state_json = json.dumps({
                "dissatisfaction_count": state.get("dissatisfaction_count", 0),
                "awaiting_email": state.get("awaiting_email", False),
                "awaiting_concern": state.get("awaiting_concern", False),
                "user_email": state.get("user_email", None)
            })
            self.collection.upsert(
                documents=[state_json],
                metadatas=[{
                    "session_id": session_id,
                    "type": "state"
                }],
                ids=[state_id]
            )
            logger.info(f"Saved session state for session {session_id}")
        except Exception as e:
            logger.error(f"Error saving session state: {e}")
            raise

    def get_session_state(self, session_id: str) -> Dict:
        try:
            results = self.collection.query(
                query_texts=[""],
                where={
                    "$and": [
                        {"session_id": {"$eq": session_id}},
                        {"type": {"$eq": "state"}}
                    ]
                },
                n_results=1
            )
            if results["documents"] and results["documents"][0]:
                state_json = results["documents"][0][0]
                state = json.loads(state_json)
                state["session_id"] = session_id
                state["messages"] = self.get_chat_history(session_id)
                logger.info(f"Retrieved session state for session {session_id}")
                return state
            # Return default state if none exists
            default_state = {
                "session_id": session_id,
                "messages": self.get_chat_history(session_id),
                "dissatisfaction_count": 0,
                "awaiting_email": False,
                "awaiting_concern": False,
                "user_email": None
            }
            logger.info(f"No session state found for session {session_id}. Returning default state.")
            return default_state
        except Exception as e:
            logger.error(f"Error retrieving session state: {e}")
            # Return default state on error
            return {
                "session_id": session_id,
                "messages": self.get_chat_history(session_id),
                "dissatisfaction_count": 0,
                "awaiting_email": False,
                "awaiting_concern": False,
                "user_email": None
            }

    def reset_collection(self):
        try:
            self.client.delete_collection("chat_history")
            self.collection = self.client.create_collection("chat_history")
            logger.info("Chat history collection reset")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise