import streamlit as st
from ui_components import initialize_ui, display_chat_messages, handle_user_input
from chat_history import ChatHistoryManager
from config import GOOGLE_API_KEY
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the Streamlit app."""
    if not GOOGLE_API_KEY:
        st.error("Please set the GOOGLE_API_KEY environment variable.")
        return
    
    # Initialize chat history manager
    chat_manager = ChatHistoryManager()
    
    initialize_ui(chat_manager)
    display_chat_messages()

    if prompt := st.chat_input("Ask me anything about the company!"):
        handle_user_input(prompt, chat_manager, st.session_state.session_id)

if __name__ == "__main__":
    main()