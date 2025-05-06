import streamlit as st
from ui_components import initialize_ui, display_chat_messages, handle_user_input, handle_voice_input
from chat_history import ChatHistoryManager
from config import GOOGLE_API_KEY
import logging
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini client
genai.configure(api_key=GOOGLE_API_KEY)

def main():
    """Main function to run the Streamlit app."""
    if not GOOGLE_API_KEY:
        st.error("Please set the GOOGLE_API_KEY environment variable.")
        return
    # Initialize chat history manager
    chat_manager = ChatHistoryManager()
    initialize_ui(chat_manager)
    # Display title after initialization
    if "company_name" in st.session_state:
        st.title(f"🏢 {st.session_state.company_name} Help Desk")
    display_chat_messages()
    if voice_prompt := handle_voice_input():
        handle_user_input(voice_prompt, chat_manager, st.session_state.session_id)
        st.rerun()
    elif prompt := st.chat_input("Ask me anything about the company!"):
        handle_user_input(prompt, chat_manager, st.session_state.session_id)

if __name__ == "__main__":
    main()