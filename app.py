import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
import streamlit as st
from RAGmodel import generate_rag_response, is_feedback_mode

st.set_page_config(page_title="EventBro", layout="centered")

st.title("🤖 EventBro")
st.write("Ask anything about the AI Workshop!")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    role, content = msg["role"], msg["content"]
    if role == "user":
        st.chat_message("user").write(content)
    else:
        st.chat_message("assistant").write(content)

# Input field for user query
query = st.chat_input("Type your message...")

user_id = "default_user"

# Handle feedback mode activation
# Handle feedback mode activation
if is_feedback_mode() and len(st.session_state.messages) == 0:
    st.session_state.feedback_step = "name"
    response = generate_rag_response("feedback_init", user_id=user_id, user_input="")
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

# Handle user input
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message("user").write(query)

    with st.spinner("Thinking..."):
        
        if is_feedback_mode():
            response = generate_rag_response("feedback_input", user_id=user_id, user_input=query)
        else:
            response = generate_rag_response(query, user_id=user_id, user_input=query)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
