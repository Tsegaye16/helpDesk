import streamlit as st
import logging
import uuid
import chromadb
import json
from chromadb.config import Settings
import speech_recognition as sr
import google.generativeai as genai
from config import INTRODUCTION_MESSAGE, GOOGLE_API_KEY, PAGE_ICON,PAGE_TITLE,CSS_FILE, GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD,EMAIL_RECIPIENT,DATA_FOLDER
from email_utils import send_support_email
from document_processor import process_documents, create_text_chunks, create_vectorstore
from llm_utils import create_conversational_chain


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Chroma DB client
chroma_client = chromadb.Client(Settings())

# Initialize Gemini client
genai.configure(api_key=GOOGLE_API_KEY)

def get_or_create_session_id() -> str:
    """Get the session ID from query params or create and store a new one."""
    session_id = st.query_params.get("session_id", [None])[0]
    if not session_id:
        session_id = str(uuid.uuid4())
        st.query_params["session_id"] = session_id
    st.session_state.session_id = session_id
    return session_id

def ensure_collection_exists(collection_name: str) -> None:
    """Ensure that the collection exists in Chroma DB."""
    if collection_name not in [col.name for col in chroma_client.list_collections()]:
        chroma_client.create_collection(collection_name)

def save_chat_message(session_id: str, message: dict) -> None:
    """Save a chat message to Chroma DB with the session ID."""
    collection_name = "chat_history"
    ensure_collection_exists(collection_name)
    collection = chroma_client.get_collection(collection_name)
    collection.add(
        documents=[json.dumps(message)],
        metadatas={"session_id": session_id, "role": message["role"]},
        ids=[str(uuid.uuid4())]
    )

def retrieve_chat_history(session_id):
    """Retrieve chat history from Chroma DB."""
    collection_name = "chat_history"
    ensure_collection_exists(collection_name)
    collection = chroma_client.get_collection(collection_name)
    results = collection.get(
        where={"session_id": session_id},
        include=["documents", "metadatas"]
    )
    messages = []
    for doc, meta in zip(results["documents"], results["metadatas"]):
        if isinstance(doc, str):
            try:
                doc_content = json.loads(doc)
                if isinstance(doc_content, dict):
                    messages.append(doc_content)
                else:
                    messages.append({"role": meta["role"], "content": str(doc)})
            except json.JSONDecodeError:
                messages.append({"role": meta["role"], "content": str(doc)})
        else:
            messages.append({"role": meta["role"], "content": str(doc)})
    return messages

def load_css(file_path: str) -> None:
    """Load and apply CSS styles."""
    try:
        with open(file_path, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error loading CSS file '{file_path}': {e}")
        st.error(f"Error loading CSS file '{file_path}': {e}")

def display_chat_messages() -> None:
    """Display chat messages in the Streamlit app."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            role_class = "user" if message["role"] == "user" else "assistant"
            prefix = "👤  " if message["role"] == "user" else "🤖  "
            st.markdown(
                f'<div class="{role_class}-message">'
                f'<div class="{role_class}-bubble"><strong>{prefix}</strong>{message["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

def handle_voice_input():
    """Handles voice input from the user."""
    if st.sidebar.button("Speak"):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.sidebar.info("Say something!")
            try:
                audio = r.listen(source, phrase_time_limit=5)
                voice_prompt = r.recognize_google(audio)
                st.sidebar.success(f"You said: {voice_prompt}")
                return voice_prompt
            except sr.WaitTimeoutError:
                st.sidebar.warning("No speech detected.")
            except sr.UnknownValueError:
                st.sidebar.error("Could not understand audio.")
            except sr.RequestError as e:
                st.sidebar.error(f"Could not request results from Google Speech Recognition service; {e}")
    return None

def detect_negative_tone(message: str) -> bool:
    """Detect negative tone using Gemini LLM."""
    try:
        # Initialize the model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=(
                "You are an expert in sentiment analysis. Analyze the sentiment of the provided message and determine if it has a negative tone. "
                "A negative tone includes expressions of frustration, dissatisfaction, anger, confusion, or disappointment. "
                "Return only 'True' if the tone is negative, or 'False' if it is neutral or positive."
            )
        )

        # Create a prompt for sentiment analysis
        prompt = (
            f"Analyze the sentiment of the following message and return 'True' if the tone is negative, or 'False' if it is neutral or positive:\n\n"
            f"Message: {message}\n\n"
            "Sentiment (True/False):"
        )

        # Generate content
        response = model.generate_content(prompt)
        sentiment = response.text.strip()

        logger.info(f"Sentiment analysis for message '{message}': {sentiment}")

        # Validate response
        if sentiment in ["True", "False"]:
            return sentiment == "True"
        else:
            logger.error(f"Invalid sentiment response: {sentiment}")
            return False  # Default to False if response is invalid

    except Exception as e:
        logger.error(f"Error detecting negative tone with LLM: {e}")
        st.error(f"Error analyzing sentiment: {e}")
        return False  # Default to False on error

def handle_user_input(prompt: str, chat_manager, session_id) -> None:
    """Handle user input and generate assistant response."""
    session_id = get_or_create_session_id()
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_chat_message(session_id, {"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(
            f'<div class="user-message">'
            f'<div class="user-bubble"><strong>👤  </strong>{prompt}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Initialize session state variables
    if "dissatisfaction_count" not in st.session_state:
        st.session_state.dissatisfaction_count = 0
    if "awaiting_email" not in st.session_state:
        st.session_state.awaiting_email = False
    if "awaiting_concern" not in st.session_state:
        st.session_state.awaiting_concern = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None

    # Check for negative tone
    if detect_negative_tone(prompt):
        st.session_state.dissatisfaction_count += 1
    else:
        st.session_state.dissatisfaction_count = 0  # Reset if positive/neutral

    # Prompt for email after 3 consecutive negative responses
    if st.session_state.dissatisfaction_count >= 3 and not st.session_state.awaiting_email:
        response = (
            "It seems like I may not be fully addressing your concern. To better assist you, "
            "please provide your email address, and I'll connect you with our support team."
        )
        st.session_state.awaiting_email = True
        with st.chat_message("assistant"):
            st.markdown(
                f'<div class="assistant-message">'
                f'<div class="assistant-bubble"><strong>🤖 </strong>{response}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_chat_message(session_id, {"role": "assistant", "content": response})
        return

    # Handle email input
    if st.session_state.awaiting_email:
        if "@" in prompt and "." in prompt:  # Basic email validation
            st.session_state.user_email = prompt
            st.session_state.awaiting_email = False
            st.session_state.awaiting_concern = True
            response = "Thank you! Please provide your specific question or concern, and I'll forward it to our support team."
        else:
            response = "Please provide a valid email address."
        with st.chat_message("assistant"):
            st.markdown(
                f'<div class="assistant-message">'
                f'<div class="assistant-bubble"><strong>🤖 </strong>{response}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_chat_message(session_id, {"role": "assistant", "content": response})
        return

    # Handle concern input and send email
    if st.session_state.awaiting_concern:
        user_concern = prompt
        st.session_state.awaiting_concern = False
        st.session_state.dissatisfaction_count = 0  # Reset counter

        # Define the function schema for Gemini
        function_declarations = [
            genai.protos.FunctionDeclaration(
                name="send_support_email",
                description="Sends an email to the support team with the user's concern.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "user_email": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "user_concern": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "recipient_email": genai.protos.Schema(type=genai.protos.Type.STRING),
                    },
                    required=["user_email", "user_concern"]
                )
            )
        ]

        # Create a Tool object
        tool = genai.protos.Tool(function_declarations=function_declarations)

        # Initialize the model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[tool],
            system_instruction="You are an assistant that sends support emails using provided tools."
        )

        try:
            # Generate content with function calling
            response = model.generate_content(
                f"Send a support email from {st.session_state.user_email} with the concern: {user_concern}"
            )

            # Process the response for function calls
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call and part.function_call.name == "send_support_email":
                        args = dict(part.function_call.args)
                        result = send_support_email(
                            user_email=args.get("user_email", st.session_state.user_email),
                            user_concern=args.get("user_concern", user_concern),
                            recipient_email=args.get("recipient_email", EMAIL_RECIPIENT)
                        )
                        response_text = result["message"]
                        break
                else:
                    response_text = "Failed to process the email request."
            else:
                response_text = "Failed to process the email request."

        except Exception as e:
            logger.error(f"Error with Gemini function calling: {e}")
            response_text = f"Failed to send email due to an error: {str(e)}"

        with st.chat_message("assistant"):
            st.markdown(
                f'<div class="assistant-message">'
                f'<div class="assistant-bubble"><strong>🤖 </strong>{response_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            save_chat_message(session_id, {"role": "assistant", "content": response_text})
        return

    # Normal response handling
    if "conversational_chain" in st.session_state:
        try:
            response_with_docs = st.session_state.conversational_chain({
                "question": prompt,
                "chat_history": st.session_state.messages
            })
            response = response_with_docs['answer'].strip()
            with st.chat_message("assistant"):
                st.markdown(
                    f'<div class="assistant-message">'
                    f'<div class="assistant-bubble"><strong>🤖 </strong>{response}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_chat_message(session_id, {"role": "assistant", "content": response})
        except Exception as e:
            error_response = "Let me try that again - sometimes connections can be tricky!"
            logger.error(f"Error processing user input: {e}")
            st.error(f"Error: {e}")
            with st.chat_message("assistant"):
                st.markdown(
                    f'<div class="assistant-message">'
                    f'<div class="assistant-bubble"><strong>🤖 </strong>{error_response}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.session_state.messages.append({"role": "assistant", "content": error_response})
                save_chat_message(session_id, {"role": "assistant", "content": error_response})
    else:
        no_data_response = f"I'm still learning about {st.session_state.company_name}. Please ensure our knowledge base is connected."
        with st.chat_message("assistant"):
            st.markdown(
                f'<div class="assistant-message">'
                f'<div class="assistant-bubble"><strong>🤖 </strong>{no_data_response}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.session_state.messages.append({"role": "assistant", "content": no_data_response})
        save_chat_message(session_id, {"role": "assistant", "content": no_data_response})

def initialize_ui(chat_manager) -> None:
    """Initialize the Streamlit UI."""
    
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)
    load_css(CSS_FILE)
    session_id = get_or_create_session_id()
    if "messages" not in st.session_state:
        st.session_state.messages = retrieve_chat_history(session_id)
    if "company_name" not in st.session_state:
        
        all_text, company_name = process_documents(DATA_FOLDER)
        st.session_state.company_name = company_name
        # st.title(f"🏢 {company_name} Help Desk")
        if not st.session_state.messages:
            st.session_state.messages.append({"role": "assistant", "content": INTRODUCTION_MESSAGE})
        if all_text:
            text_chunks = create_text_chunks(all_text)
            vectorstore = create_vectorstore(text_chunks)
            st.session_state.conversational_chain = create_conversational_chain(vectorstore, company_name)
    st.sidebar.title("Voice Input")
    st.sidebar.markdown("Click the button below to speak.")