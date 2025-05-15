from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from typing import Dict, List
from config import GOOGLE_API_KEY, DATA_FOLDER, GEMINI_MODEL_NAME,EMAIL_RECIPIENT
from document_processor import process_documents, create_text_chunks, create_vectorstore
from llm_utils import create_conversational_chain, extract_company_name
from chat_history import ChatHistoryManager
from email_utils import send_support_email
import uuid

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=GOOGLE_API_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: str = None

class ChatResponse(BaseModel):
    result: str
    session_id: str

class SessionResponse(BaseModel):
    session_id: str

# Global variables (initialized on startup)
chat_manager = ChatHistoryManager()
vectorstore = None
conversational_chain = None
company_name = None
support_email = None

@app.on_event("startup")
async def startup_event():
    global vectorstore, conversational_chain, company_name, support_email
    try:
        all_text, company_name, support_email = process_documents(DATA_FOLDER)
        text_chunks = create_text_chunks(all_text)
        vectorstore = create_vectorstore(text_chunks)
        conversational_chain = create_conversational_chain(vectorstore, company_name)
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

# Session state management
def get_session_state(session_id: str) -> Dict:
    if not session_id:
        session_id = chat_manager.generate_session_id()
    return chat_manager.get_session_state(session_id)

def detect_negative_tone(message: str) -> bool:
    try:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            system_instruction=(
                "You are an expert in sentiment analysis. Analyze the sentiment of the provided message and determine if it has a negative tone. "
                "A negative tone includes expressions of frustration, dissatisfaction, anger, confusion, disappointment, or negation. "
                "Return 'True' if the tone is negative, or 'False' if it is neutral or positive. Ensure the response is exactly 'True' or 'False'."
            )
        )
        prompt = (
            f"Analyze the sentiment of the following message and return exactly 'True' if the tone is negative, or 'False' if it is neutral or positive:\n\n"
            f"Message: {message}\n\n"
            "Sentiment (True/False):"
        )
        response = model.generate_content(prompt)
        sentiment = response.text.strip().lower()
        if sentiment not in ["true", "false"]:
            logger.warning(f"Invalid sentiment response from LLM: {sentiment}. Falling back to keyword analysis.")
            negative_keywords = [
                "not helpful", "wrong", "bad", "terrible", "awful", "frustrated", 
                "disappointed", "angry", "confused", "hate", "don't like", "no", 
                "can't", "stupid", "fail", "useless", "didn't", "doesn’t", "never"
            ]
            return any(keyword in message.lower() for keyword in negative_keywords)
        logger.info(f"Sentiment analysis for message '{message}': {sentiment}")
        return sentiment == "true"
    except Exception as e:
        logger.error(f"Error detecting negative tone with LLM: {e}")
        negative_keywords = [
            "not helpful", "wrong", "bad", "terrible", "awful", "frustrated", 
            "disappointed", "angry", "confused", "hate", "don't like", "no", 
            "can't", "stupid", "fail", "useless", "didn't", "doesn’t", "never"
        ]
        return any(keyword in message.lower() for keyword in negative_keywords)


@app.get("/getCompanyName")
async def get_company_name():
    try:
        return {
            "status": "success",
            "result": {
                "company_name": company_name
            }
        }
    except Exception as e:
        logger.error(f"Error fetching company name: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch company name")

@app.post("/initSession", response_model=SessionResponse)
async def init_session():
    try:
        session_id = chat_manager.generate_session_id()
        logger.info(f"Initialized new session with ID: {session_id}")
        return SessionResponse(session_id=session_id)
    except Exception as e:
        logger.error(f"Error initializing session: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize session")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or chat_manager.generate_session_id()
        state = get_session_state(session_id)
        
        # Save user message
        chat_manager.save_chat_message(session_id, "user", request.message)
        state["messages"].append({"role": "user", "content": request.message})

        # Update dissatisfaction count
        if detect_negative_tone(request.message):
            state["dissatisfaction_count"] += 1
            logger.info(f"Negative tone detected. Dissatisfaction count: {state['dissatisfaction_count']} for session {session_id}")
        else:
            state["dissatisfaction_count"] = 0
            logger.info(f"Non-negative tone detected. Resetting dissatisfaction count to 0 for session {session_id}")

        # Handle escalation after 3 negative responses
        if state["dissatisfaction_count"] >= 3 and not state["awaiting_email"]:
            state["awaiting_email"] = True
            response = (
                "It seems like I may not be fully addressing your concern. To better assist you, "
                "please provide your email address, and I'll connect you with our support team."
            )
            logger.info(f"Escalation triggered: Requesting email for session {session_id}")
            chat_manager.save_chat_message(session_id, "assistant", response)
            chat_manager.save_session_state(session_id, state)
            return ChatResponse(result=response, session_id=session_id)

        # Handle email input
        if state["awaiting_email"]:
            if "@" in request.message and "." in request.message:
                state["user_email"] = request.message
                state["awaiting_email"] = False
                state["awaiting_concern"] = True
                response = "Thank you! Please provide your specific question or concern, and I'll forward it to our support team."
                logger.info(f"Email received: {state['user_email']} for session {session_id}")
            else:
                response = "Please provide a valid email address."
                logger.info(f"Invalid email provided for session {session_id}")
            chat_manager.save_chat_message(session_id, "assistant", response)
            chat_manager.save_session_state(session_id, state)
            return ChatResponse(result=response, session_id=session_id)

        # Handle concern input and send email
        if state["awaiting_concern"]:
            user_concern = request.message
            state["awaiting_concern"] = False
            state["dissatisfaction_count"] = 0

            # Use extracted support email if available, else fall back to EMAIL_RECIPIENT
            recipient = support_email if support_email else EMAIL_RECIPIENT
            result = send_support_email(
                state["user_email"],
                user_concern,
                recipient_email=recipient,
                chat_history=state["messages"]  # Pass chat history
            )
            response = result["message"]
            logger.info(f"Support email sent for session {session_id}: {response}")
            chat_manager.save_chat_message(session_id, "assistant", response)
            chat_manager.save_session_state(session_id, state)
            return ChatResponse(result=response, session_id=session_id)

        # Normal response handling
        try:
            response_with_docs = conversational_chain.invoke({
                "question": request.message,
                "chat_history": state["messages"]
            })
            response = response_with_docs['answer'].strip()
            chat_manager.save_chat_message(session_id, "assistant", response)
            chat_manager.save_session_state(session_id, state)
            logger.info(f"Normal response generated for session {session_id}")
            return ChatResponse(result=response, session_id=session_id)
        except Exception as e:
            error_response = "Let me try that again - sometimes connections can be tricky!"
            logger.error(f"Error processing user input: {e}")
            chat_manager.save_chat_message(session_id, "assistant", error_response)
            chat_manager.save_session_state(session_id, state)
            return ChatResponse(result=error_response, session_id=session_id)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        chat_manager.save_session_state(session_id, state)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/getChatHistory/{session_id}")
async def get_chat_history(session_id: str):
    try:
        history = chat_manager.get_chat_history(session_id)
        
        return {
            "status": "success",
            "result": {
                "messages": [
                    {"sender": msg["role"], "text": msg["content"]}
                    for msg in history
                ],
                "session_id": session_id
            }
        }
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat history")