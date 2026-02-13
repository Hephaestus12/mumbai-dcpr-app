import streamlit as st
import os

# --- ENV SETUP (Must be before importing core modules) ---
# Inject Streamlit secrets into os.environ for domain.config to pick them up
# This is crucial for Streamlit Cloud where .env isn't used but secrets are
if hasattr(st, "secrets"):
    for key, value in st.secrets.items():
        if isinstance(value, str):
            os.environ[key] = value

from streamlit_feedback import streamlit_feedback
from core.retrieval import get_rag_chain
from langchain_core.messages import HumanMessage, AIMessage
import time
import json
import datetime
import uuid

# --- LOGGING SETUP ---
def log_event(session_id, event_type, data=None):
    """Log an event in JSON format."""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "session_id": session_id,
        "event_type": event_type,
        "data": data or {}
    }
    print(json.dumps(log_entry))

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DCPR 2034 Bot", 
    page_icon="📓",
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Override primary button color in sidebar to be Grey */
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #607D8B !important;
        border-color: #607D8B !important;
        color: white !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #455A64 !important;
        border-color: #455A64 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SECURITY & LOGIN ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if "password" in st.session_state and st.session_state["password"] == st.secrets["ACCESS_CODE"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        col_img1, col_img2, col_img3 = st.columns([1, 1, 1])
        with col_img2:
            st.image("assets/heading.png", width="stretch")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Access Restricted")
            st.write("This is a private tool for testing purposes only. If you have been given the link, please reach out to the person who shared it for the access code.")
            st.text_input(
                "Enter Access Code:", type="password", on_change=password_entered, key="password"
            )
            # st.caption("Built by Tej Sukhatme")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error.
        col_img1, col_img2, col_img3 = st.columns([1, 1, 1])
        with col_img2:
            st.image("assets/heading.png", width="stretch")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Access Restricted")
            st.write("This is a private tool for testing purposes only. If you have been given the link, please reach out to the person who shared it for the access code.")
            st.text_input(
                "Enter Access Code:", type="password", on_change=password_entered, key="password"
            )
            st.error("Access Code incorrect")
            # st.caption("Built by Tej Sukhatme")
        return False
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()  # Do not run the rest of the app if not authenticated

# --- CHAT STATE INIT ---
# Initialize chat history state
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    new_chat_id = str(uuid.uuid4())
    st.session_state.chats[new_chat_id] = {
        "messages": [],
        "title": f"Chat {datetime.datetime.now().strftime('%H:%M')}"
    }
    st.session_state.current_chat_id = new_chat_id

if "session_id" not in st.session_state:
    st.session_state.session_id = str(time.time())

def get_current_chat():
    return st.session_state.chats[st.session_state.current_chat_id]

# --- SIDEBAR & DISCLAIMER ---
with st.sidebar:
    st.header("Mumbai DCPR 2034 Chat Assistant")
    st.markdown("### ⚠️ Disclaimer")
    st.warning(
        "This AI tool is for **informational purposes only**.\n\n"
        "Always consult the official [Gazette of DCPR 2034](https://mchi.net/wp-content/uploads/2022/07/comprehensive-dcpr-2034-peata.pdf) "
        "or a licensed architect/surveyor for legal validation."
    )
    
    st.markdown("---")
    st.markdown("### 📖 How to Use")
    st.markdown(
        "Ask questions about:\n"
        "- **FSI Rules** (e.g., *'What is the base FSI for residential?'*)\n"
        "- **Side Margins** & Open Spaces\n"
        "- **Specific Regulations** (e.g., *'Explain Regulation 33(7)'*)\n"
        "- **Definitions** (e.g., *'What is a habitable room?'*)"
    )
    st.markdown("---")
    if st.button("Clear Chat History", use_container_width=True):
        get_current_chat()["messages"] = []
        st.rerun()

# --- MAIN APP UI ---
st.image("assets/heading.png", width="stretch")

st.header("DCPR 2034 Chat Assistant")
# st.caption("Built by Tej Sukhatme")



# --- SIDEBAR CHAT HISTORY ---
with st.sidebar:
    st.markdown("---")
    if st.button("➕ New Chat", use_container_width=True):
        new_chat_id = str(uuid.uuid4())
        st.session_state.chats[new_chat_id] = {
            "messages": [],
            "title": f"Chat {datetime.datetime.now().strftime('%H:%M')}"
        }
        st.session_state.current_chat_id = new_chat_id
        st.rerun()
    
    st.markdown("### Recent Chats")
    # Display chat history buttons
    for chat_id, chat_data in list(st.session_state.chats.items())[::-1]: # Reverse order
        # Simple title based on first message or timestamp
        if len(chat_data["messages"]) > 0:
            title = chat_data["messages"][0]["content"][:20] + "..."
        else:
            title = chat_data["title"]
            
        if st.button(title, key=chat_id, use_container_width=True, 
                     type="primary" if chat_id == st.session_state.current_chat_id else "secondary"):
            st.session_state.current_chat_id = chat_id
            st.rerun()

# Load RAG Chain
@st.cache_resource
def load_chain():
    return get_rag_chain()

try:
    rag_chain = load_chain()
except Exception as e:
    st.error(f"Error loading RAG chain: {e}")
    st.stop()

# Display chat messages from history on app rerun
current_chat = get_current_chat()
for n, message in enumerate(current_chat["messages"]):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # If it was an assistant message, show the sources if preserved in history (optional complexity)
        # For simplicity, we just show sources immediately after generation below. 
        # But if we wanted persistent sources, we'd need to store them in session_state.messages.
        if message.get("sources"):
             with st.expander("View Source Regulations"):
                for idx, src in enumerate(message["sources"]):
                     st.markdown(f"**Source {idx+1} (Reg: {src.get('regulation_id', 'N/A')}):**")
                     st.text(src.get('text', '')[:300] + "...")

# React to user input
if prompt := st.chat_input("Ask a question about Mumbai Development Control Regulations..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    current_chat["messages"].append({"role": "user", "content": prompt})

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing regulations..."):
            try:
                # Log the question start
                log_event(st.session_state.session_id, "user_query", {"input": prompt})
                
                # Format history for LangChain
                chat_history = []
                for msg in current_chat["messages"][:-1]: # Exclude the just added user message
                    if msg["role"] == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        chat_history.append(AIMessage(content=msg["content"]))

                response = rag_chain.invoke({"input": prompt, "chat_history": chat_history})
                answer = response["answer"]
                documents = response["context"]
                
                # Display answer
                st.markdown(answer)
                
                # Process sources for display & storage
                sources_data = []
                with st.expander("View Source Regulations"):
                    for i, doc in enumerate(documents):
                        # Extract metadata safely
                        reg_id = doc.metadata.get('regulation_id', 'N/A')
                        page = doc.metadata.get('page_number', 'N/A')
                        snippet = doc.page_content
                        
                        st.markdown(f"**Source {i+1} (Reg: {reg_id}, Page: {page}):**")
                        st.text(snippet[:400] + "...")
                        
                        sources_data.append({
                            "regulation_id": reg_id,
                            "page": page,
                            "text": snippet
                        })
                
                # Log the answer
                log_event(st.session_state.session_id, "ai_response", {"answer": answer, "sources_count": len(sources_data)})
                
                # Save to history
                current_chat["messages"].append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources_data
                })
                
                # Trigger feedback
                # Note: streamlit_feedback works best when it's the last element. 
                # We can't easily embed it *inside* the chat loop for *historical* messages easily without complications.
                # So we usually show it for the *latest* response or use a specific key.
                
            except Exception as e:
                st.error(f"Error: {e}")
                log_event(st.session_state.session_id, "error", {"error_message": str(e)})

# Feedback for the LATEST assistant message (outside the loop to ensure it renders at bottom)
if len(current_chat["messages"]) > 0 and current_chat["messages"][-1]["role"] == "assistant":
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label="[Optional] Please provide explanation",
        key=f"feedback_{len(current_chat['messages'])}",
    )
    
    if feedback:
        score = feedback["score"] # '👍' or '👎' usually, or mapped values
        text = feedback.get("text", "")
        log_event(st.session_state.session_id, "user_feedback", {"score": score, "comments": text})
        st.toast("Thank you for your feedback!", icon="🙏")
