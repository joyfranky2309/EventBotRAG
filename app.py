import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
import streamlit as st
from RAGmodel import generate_rag_response, is_feedback_mode

# Page config
st.set_page_config(page_title="EventBro", layout="centered")

# Custom CSS for classy look
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #e3f2fd, #ffffff);
        font-family: 'Segoe UI', sans-serif;
    }
    .chat-message {
        border-radius: 15px;
        padding: 12px 20px;
        margin: 10px 0;
        max-width: 85%;
        box-shadow: 0 4px 8px rgba(0,0,0,0.06);
    }
    .chat-message.user {
        background-color: #d1e7dd;
        margin-left: auto;
        color: #1b4332;
    }
    .chat-message.assistant {
        background-color: #f1f3f5;
        margin-right: auto;
        color: #343a40;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align: center;'>🤖 EventBro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:18px;'>Ask anything about the AI Workshop!</p>", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for msg in st.session_state.messages:
    role = msg["role"]
    bubble_class = "user" if role == "user" else "assistant"
    st.markdown(
        f"<div class='chat-message {bubble_class}'>{msg['content']}</div>",
        unsafe_allow_html=True
    )

# Input
query = st.chat_input("Type your message...")

user_id = "default_user"

# Feedback init
if is_feedback_mode() and len(st.session_state.messages) == 0:
    st.session_state.feedback_step = "name"
    response = generate_rag_response("feedback_init", user_id=user_id, user_input="")
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.markdown(f"<div class='chat-message assistant'>{response}</div>", unsafe_allow_html=True)

# Query handling
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    st.markdown(f"<div class='chat-message user'>{query}</div>", unsafe_allow_html=True)

    with st.spinner("Thinking..."):
        if is_feedback_mode():
            response = generate_rag_response("feedback_input", user_id=user_id, user_input=query)
        else:
            response = generate_rag_response(query, user_id=user_id, user_input=query)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.markdown(f"<div class='chat-message assistant'>{response}</div>", unsafe_allow_html=True)
    