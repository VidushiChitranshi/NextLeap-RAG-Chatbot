import streamlit as st
import os
import sys

# ── Streamlit Cloud SQLite Fix ─────────────────────────────────────────────
# Streamlit Cloud's default SQLite version is often too old for ChromaDB.
# This wrapper swaps it for a modern version if pysqlite3-binary is installed.
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from dotenv import load_dotenv
from main import build_chatbot

# ── Load Environment ──────────────────────────────────────────────────────
# Prioritise Streamlit Secrets if available (for Cloud), else use .env
load_dotenv()

try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except (FileNotFoundError, KeyError, Exception):
    # This handles StreamlitSecretNotFoundError or missing keys silently
    # as we already have fallbacks from load_dotenv()
    pass

# ── Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="NextLeap RAG Chatbot",
    page_icon="🚀",
    layout="centered",
)

# ── Styling ──────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    .stChatMessage {
        border-radius: 15px;
        margin-bottom: 10px;
    }
    .stSidebar {
        background-color: #f0f2f6;
    }
    .citation-label {
        font-size: 0.8rem;
        color: #555;
        background-color: #e0e0e0;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ── Load Environment ──────────────────────────────────────────────────────
load_dotenv()

# ── Initialize Chatbot ────────────────────────────────────────────────────
@st.cache_resource
def get_chatbot():
    try:
        return build_chatbot()
    except Exception as e:
        st.error(f"Failed to initialize chatbot: {e}")
        return None

chatbot = get_chatbot()

# ── Session State ──────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! How may I help you?\n\nYou can ask questions related to :\n1. Different Courses offered by NextLeap\n2. Important dates related to various courses\n3. Instructors of NextLeap\n4. Mentors for different courses"}]

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("NextLeap AI 🚀")
    st.markdown("Your personal guide to NextLeap fellowships.")
    
    if st.button("Clear Conversation History"):
        if chatbot:
            chatbot.clear_history()
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.markdown("### About")
    st.info(
        "This chatbot uses a RAG (Retrieval-Augmented Generation) pipeline "
        "powered by Groq (Llama 3.3) and Gemini Embeddings."
    )

# ── Chat Interface ────────────────────────────────────────────────────────
st.title("NextLeap Chatbot")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            st.markdown("---")
            st.markdown("**Sources:**")
            citations_html = ""
            for c in message["citations"]:
                if c.startswith("http"):
                    citations_html += f'<a href="{c}" target="_blank" class="citation-label" style="text-decoration: none;">🔗 Source</a>'
                else:
                    citations_html += f'<span class="citation-label">{c}</span>'
            st.markdown(citations_html, unsafe_allow_html=True)

# Accept user input
if prompt := st.chat_input("Ask me about the PM fellowship..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Searching for information...")
        
        if not chatbot:
            full_response = "Error: Chatbot not initialized."
            citations = []
        else:
            try:
                reply = chatbot.chat(prompt)
                if reply.success:
                    full_response = reply.answer
                    citations = reply.citations
                else:
                    full_response = f"I encountered an error: {reply.error}"
                    citations = []
            except Exception as e:
                full_response = f"An unexpected error occurred: {e}"
                citations = []

        message_placeholder.markdown(full_response)
        
        if citations:
            st.markdown("---")
            st.markdown("**Sources:**")
            citations_html = ""
            for c in citations:
                if c.startswith("http"):
                    citations_html += f'<a href="{c}" target="_blank" class="citation-label" style="text-decoration: none;">🔗 Source</a>'
                else:
                    citations_html += f'<span class="citation-label">{c}</span>'
            st.markdown(citations_html, unsafe_allow_html=True)
            
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": full_response,
            "citations": citations
        })
