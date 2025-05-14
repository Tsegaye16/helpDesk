from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
import streamlit as st
import logging
from config import GOOGLE_API_KEY, GEMINI_MODEL_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_company_name(text: str) -> str:
    """Extract the company name from the document text using an LLM."""
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        convert_system_message_to_human=True
    )
    
    first_paragraphs = text[:1000]  # Limit to first 1000 characters
    prompt = (
        "You are an expert at extracting information from text. Given the following text from a company document, "
        "identify the name of the company. The company name may appear in titles, introductions, or as part of phrases "
        "like 'About [Company]', 'Welcome to [Company]', or as a proper noun with terms like 'Inc.', 'LLC', 'Corp', etc. "
        "Return only the company name as a string. If no company name is found, return 'our company'.\n\n"
        f"Text: {first_paragraphs}\n\n"
        "Company Name:"
    )
    
    try:
        response = llm.invoke(prompt)
        company_name = response.content.strip()
        if company_name and company_name.lower() not in ["", "company", "organization", "none"]:
            return company_name
        return "our company"
    except Exception as e:
        logger.error(f"Error extracting company name with LLM: {e}")
        st.error(f"Error extracting company name with LLM: {e}")
        return "our company"

def extract_support_email(text: str) -> str:
    """Extract the support team email from the document text using an LLM."""
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        convert_system_message_to_human=True
    )
    
    # Use full text to increase chances of finding email
    prompt = (
        "You are an expert at extracting information from text. Given the following text from a company document, "
        "identify the email address associated with the support team or customer service. The email may appear in phrases "
        "like 'contact support at', 'email us at', 'support@company.com', or in sections like 'Contact Us', 'Support', or 'Help'. "
        "Return only the email address as a string. If no support email is found, return an empty string.\n\n"
        f"Text: {text}\n\n"
        "Support Email:"
    )
    
    try:
        response = llm.invoke(prompt)
        email = response.content.strip()
        # Basic email validation
        if email and "@" in email and "." in email:
            return email
        return ""
    except Exception as e:
        logger.error(f"Error extracting support email with LLM: {e}")
        st.error(f"Error extracting support email with LLM: {e}")
        return ""

def create_conversational_chain(vectorstore, company_name: str) -> ConversationalRetrievalChain:
    """Create a conversational retrieval chain for the chatbot."""
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        convert_system_message_to_human=True
    )
    
    custom_template = f"""You are the primary AI assistant for {company_name}, designed to deliver exceptional support with accuracy and emotional intelligence.

# Core Responsibilities
1. **Knowledge Expert**: Provide accurate, reliable information based on {company_name}'s documents and context.
2. **User Satisfaction Monitor**: Implicitly gauge user satisfaction from their tone and responses.

# Operating Guidelines
- Maintain a warm, professional, and friendly tone in all interactions.
- Respond only in English, even if the user uses another language.
- Analyze each user message for tone and satisfaction level to tailor responses.
- For normal queries, provide clear, concise, and accurate information.
- If the user expresses dissatisfaction (e.g., frustration, confusion, or negative tone):
  - Acknowledge their concern empathetically.
  - Offer improved assistance or clarification.
- If the user continues to express dissatisfaction, suggest contacting support directly.

# Conversation History
{{chat_history}}

# Company Context
{{context}}

# Current Interaction
User: {{question}}

# Response Strategy
1. **Analyze Tone and Satisfaction**:
   - Detect the user's emotional state (e.g., satisfied, neutral, frustrated) based on their message.
   - Adjust your response to address their needs and emotions.
2. **Handle Dissatisfaction**:
   - If dissatisfied, respond empathetically and offer a solution or clarification.
   - If dissatisfaction persists, suggest: "It seems like I may not be fully addressing your concern. Please consider contacting our support team directly for further assistance."
3. **Normal Interaction**:
   - Provide accurate, helpful information.
   - Maintain a natural, engaging conversation flow.

Response:"""
    
    QA_PROMPT = PromptTemplate(
        template=custom_template, 
        input_variables=["chat_history", "context", "question"]
    )
    
    memory = ConversationBufferMemory(
        memory_key='chat_history',
        return_messages=True,
        output_key='answer',
        input_key='question'
    )
    
    try:
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            memory=memory,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT}
        )
        logger.info("Conversational chain created successfully")
        return chain
    except Exception as e:
        logger.error(f"Error creating conversational chain: {e}")
        st.error(f"Error creating conversational chain: {e}")
        raise