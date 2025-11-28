import streamlit as st
from rag_agent import RAGAgent

# Set page configuration
st.set_page_config(
    page_title="MENA Tourist Chat Assistant",
    page_icon="🤖",
    layout="centered"
)

# Initialize the RAG agent
@st.cache_resource
def load_agent():
    return RAGAgent()

# App title and description
st.title("🤖 MENA Tourist Chat Assistant")
st.markdown("Ask me anything about MENA region!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What would you like to know?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get agent response with loading indicator
    with st.spinner("Thinking..."):
        agent = load_agent()
        response = agent.ask(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})