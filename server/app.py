from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import json
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from typing import Dict, List
import re
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

def detect_negative_tone(message: str) -> tuple[bool, bool]:
    try:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            system_instruction=(
                "You are an expert in sentiment analysis and intent detection. Analyze the provided message for two aspects:\n"
                "1. **Negative Tone**: Determine if the message has a negative tone, including expressions of frustration, dissatisfaction, anger, confusion, disappointment, or negation.\n"
                "2. **Support Request**: Determine if the message explicitly requests contact with the support team, such as phrases like 'contact support', 'email support', 'talk to support', 'send to support', or similar.\n"
                "Return a JSON object with two fields: 'is_negative' (true/false) and 'is_support_request' (true/false). Ensure the response is valid JSON."
            )
        )
        prompt = (
            f"Analyze the following message:\n\n"
            f"Message: {message}\n\n"
            "Return: ```json\n"
            "{\"is_negative\": <true/false>, \"is_support_request\": <true/false>}\n"
            "```"
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip().lstrip("```json").rstrip("```"))
        
        if not isinstance(result, dict) or "is_negative" not in result or "is_support_request" not in result:
            logger.warning(f"Invalid response from LLM: {response.text}. Falling back to keyword analysis.")
            return fallback_analysis(message)
        
        logger.info(f"Sentiment analysis for message '{message}': {result}")
        return result["is_negative"], result["is_support_request"]
    except Exception as e:
        logger.error(f"Error detecting tone or support request with LLM: {e}")
        return fallback_analysis(message)

def fallback_analysis(message: str) -> tuple[bool, bool]:
    negative_keywords = [
        "not helpful", "wrong", "bad", "terrible", "awful", "frustrated", 
        "disappointed", "angry", "confused", "hate", "don't like", "no", 
        "can't", "stupid", "fail", "useless", "didn't", "doesn’t", "never"
    ]
    support_keywords = [
        "contact support", "email support", "talk to support", "send to support", 
        "support team", "customer service", "help desk", "escalate", "human agent"
    ]
    is_negative = any(keyword in message.lower() for keyword in negative_keywords)
    is_support_request = any(keyword in message.lower() for keyword in support_keywords)
    return is_negative, is_support_request

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
        logger.debug(f"Initial state for session {session_id}: {state}")

        # Save user message
        chat_manager.save_chat_message(session_id, "user", request.message)
        state["messages"].append({"role": "user", "content": request.message})

        # Handle email confirmation first to ensure it’s not skipped
        if state.get("awaiting_email_confirmation", False):
            user_response = request.message.lower().strip()
            logger.info(f"Confirmation response received: '{user_response}' for session {session_id}")
            if user_response in ["yes", "confirm", "ok", "send"]:
                # Send the email
                recipient = support_email if support_email else EMAIL_RECIPIENT
                result = send_support_email(
                    state["user_email"],
                    state["user_concern"],
                    recipient_email=recipient,
                    chat_history=state["messages"]
                )
                state["awaiting_email_confirmation"] = False
                state["dissatisfaction_count"] = 0
                response = result["message"]
                if result["status"] == "error":
                    response = f"Failed to send email: {result['message']}. Please try again or contact support directly."
                logger.info(f"Support email sent for session {session_id}: {response}")
            elif user_response in ["no", "cancel", "stop"]:
                # Cancel the email
                state["awaiting_email_confirmation"] = False
                state["dissatisfaction_count"] = 0
                response = "Email sending canceled. How else can I assist you?"
                logger.info(f"Email sending canceled for session {session_id}")
            else:
                # Treat as a revised concern and recompose preview
                state["user_concern"] = request.message
                recipient = support_email if support_email else EMAIL_RECIPIENT
                email_body = f"User Email: {state['user_email']}\n\nConcern:\n{state['user_concern']}\n\nRecent Conversation (Last 3 Exchanges):\n"
                recent_messages = state["messages"][-6:]
                if recent_messages:
                    for msg in recent_messages:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        email_body += f"{role}: {msg['content']}\n"
                else:
                    email_body += "No recent conversation available.\n"

                response = (
                    "Here’s the updated email preview with your revised concern:\n\n"
                    f"---\n"
                    f"Subject: Support Request from {state['user_email']}\n"
                    f"To: {recipient}\n\n"
                    f"{email_body}"
                    f"---\n\n"
                    "Please confirm by replying 'yes', 'confirm', 'ok', or 'send' to send the email. "
                    "Reply 'no', 'cancel', or 'stop' to cancel, or provide another concern to revise again."
                )
                logger.info(f"Email preview updated with revised concern for session {session_id}")
            chat_manager.save_chat_message(session_id, "assistant", response)
            chat_manager.save_session_state(session_id, state)
            logger.debug(f"State after confirmation handling for session {session_id}: {state}")
            return ChatResponse(result=response, session_id=session_id)

        # Update dissatisfaction count or trigger support request
        is_negative, is_support_request = detect_negative_tone(request.message)
        if is_negative:
            state["dissatisfaction_count"] += 1
            logger.info(f"Negative tone detected. Dissatisfaction count: {state['dissatisfaction_count']} for session {session_id}")
        else:
            state["dissatisfaction_count"] = 0
            logger.info(f"Non-negative tone detected. Resetting dissatisfaction count to 0 for session {session_id}")

        # Handle escalation: either 3 negative responses or explicit support request
        if (state["dissatisfaction_count"] >= 3 or is_support_request) and not state.get("awaiting_email", False):
            state["awaiting_email"] = True
            response = (
                "It seems like you’d like to connect with our support team. "
                "Please provide your email address, and I'll forward your request."
            )
            logger.info(f"Escalation triggered: {'Support request' if is_support_request else '3 negative responses'} for session {session_id}")
            chat_manager.save_chat_message(session_id, "assistant", response)
            chat_manager.save_session_state(session_id, state)
            logger.debug(f"State after escalation for session {session_id}: {state}")
            return ChatResponse(result=response, session_id=session_id)

        # Handle email input
        if state.get("awaiting_email", False):
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', request.message):
                state["user_email"] = request.message
                state["awaiting_email"] = False
                state["awaiting_concern"] = True
                response = "Thank you! Please provide your specific question or concern, and I'll forward it to our support team."
                logger.info(f"Email received: {state['user_email']} for session {session_id}")
            else:
                response = "Please provide a valid email address (e.g., user@example.com)."
                logger.info(f"Invalid email provided for session {session_id}: {request.message}")
            chat_manager.save_chat_message(session_id, "assistant", response)
            chat_manager.save_session_state(session_id, state)
            logger.debug(f"State after email input for session {session_id}: {state}")
            return ChatResponse(result=response, session_id=session_id)

        # Handle concern input and compose email preview
        if state.get("awaiting_concern", False):
            state["user_concern"] = request.message
            state["awaiting_concern"] = False
            state["awaiting_email_confirmation"] = True

            # Compose email preview
            recipient = support_email if support_email else EMAIL_RECIPIENT
            email_body = f"User Email: {state['user_email']}\n\nConcern:\n{state['user_concern']}\n\nRecent Conversation (Last 3 Exchanges):\n"
            recent_messages = state["messages"][-6:]  # Last 6 to cover 3 user-assistant pairs
            if recent_messages:
                for msg in recent_messages:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    email_body += f"{role}: {msg['content']}\n"
            else:
                email_body += "No recent conversation available.\n"

            response = (
                "Here’s a preview of the email that will be sent to our support team:\n\n"
                f"---\n"
                f"Subject: Support Request from {state['user_email']}\n"
                f"To: {recipient}\n\n"
                f"{email_body}"
                f"---\n\n"
                "Please confirm by replying 'yes', 'confirm', 'ok', or 'send' to send the email. "
                "Reply 'no', 'cancel', or 'stop' to cancel, or provide another concern to revise."
            )
            logger.info(f"Email preview presented for session {session_id}")
            chat_manager.save_chat_message(session_id, "assistant", response)
            chat_manager.save_session_state(session_id, state)
            logger.debug(f"State after preview for session {session_id}: {state}")
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
            logger.debug(f"State after normal response for session {session_id}: {state}")
            return ChatResponse(result=response, session_id=session_id)
        except Exception as e:
            error_response = "Let me try that again - sometimes connections can be tricky!"
            logger.error(f"Error processing user input: {e}")
            chat_manager.save_chat_message(session_id, "assistant", error_response)
            chat_manager.save_session_state(session_id, state)
            logger.debug(f"State after error response for session {session_id}: {state}")
            return ChatResponse(result=error_response, session_id=session_id)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        chat_manager.save_session_state(session_id, state)
        logger.debug(f"State after error for session {session_id}: {state}")
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