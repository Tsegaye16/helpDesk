import os

# Environment variables
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")

# Model configurations
GEMINI_MODEL_NAME = "gemini-2.0-flash"
EMBEDDING_MODEL_NAME = "models/embedding-001"

# App configurations
INTRODUCTION_MESSAGE = "Hello! Welcome to the company help desk. How can I assist you today?"
DATA_FOLDER = "data"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
PAGE_TITLE = "Company Help Desk"
PAGE_ICON = "🏢"
CSS_FILE = "style.css"
CHROMA_PERSIST_DIR = "chroma_db"
GMAIL_SENDER_EMAIL = os.environ.get("EMAIL_SENDER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_SENDER_EMAIL")


