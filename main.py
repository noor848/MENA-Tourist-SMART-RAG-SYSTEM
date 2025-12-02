import streamlit as st
from rag_agent import RAGAgent

# Set page configuration
st.set_page_config(
    page_title="MENA Tourist Chat Assistant",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for stunning MENA-inspired design
st.markdown("""
<style>
    /* Import elegant fonts */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Outfit:wght@300;400;500;600&display=swap');

    /* Root variables for MENA-inspired color palette */
    :root {
        --gold-primary: #D4A853;
        --gold-light: #E8C97A;
        --gold-dark: #B8923F;
        --desert-sand: #F5E6D3;
        --terracotta: #C67B5C;
        --deep-blue: #1A2B4A;
        --midnight: #0D1321;
        --ivory: #FDF8F0;
        --copper: #B87333;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main container styling with background */
    .stApp {
        background: linear-gradient(135deg, var(--midnight) 0%, var(--deep-blue) 50%, #2A3B5A 100%);
        min-height: 100vh;
    }

    /* Geometric pattern overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 0L60 30L30 60L0 30L30 0z' fill='none' stroke='%23D4A85315' stroke-width='1'/%3E%3C/svg%3E"),
            url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='50' cy='50' r='40' fill='none' stroke='%23D4A85308' stroke-width='1'/%3E%3C/svg%3E");
        pointer-events: none;
        z-index: 0;
    }

    /* Decorative corner ornaments */
    .stApp::after {
        content: '✦';
        position: fixed;
        top: 20px;
        right: 30px;
        font-size: 2rem;
        color: var(--gold-primary);
        opacity: 0.6;
        animation: sparkle 3s ease-in-out infinite;
    }

    @keyframes sparkle {
        0%, 100% { opacity: 0.3; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.1); }
    }

    /* Main content area - wider */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1200px !important;
        width: 100% !important;
        position: relative;
        z-index: 1;
    }

    /* Ensure chat area is full width */
    .stChatMessageContainer {
        width: 100% !important;
        max-width: 100% !important;
    }

    /* Custom header styling */
    .hero-section {
        text-align: center;
        padding: 3rem 2rem;
        margin-bottom: 2rem;
        background: linear-gradient(180deg, rgba(212, 168, 83, 0.1) 0%, transparent 100%);
        border-radius: 24px;
        border: 1px solid rgba(212, 168, 83, 0.2);
        position: relative;
        overflow: hidden;
    }

    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(212, 168, 83, 0.05) 0%, transparent 50%);
        animation: rotate 30s linear infinite;
    }

    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-weight: 600;
        background: linear-gradient(135deg, var(--gold-light) 0%, var(--gold-primary) 50%, var(--copper) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
        text-shadow: 0 0 40px rgba(212, 168, 83, 0.3);
    }

    .hero-subtitle {
        font-family: 'Outfit', sans-serif;
        font-size: 1.1rem;
        color: var(--desert-sand);
        opacity: 0.9;
        font-weight: 300;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        position: relative;
        z-index: 1;
    }

    .hero-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        display: block;
        animation: float 4s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    /* Decorative divider */
    .divider {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 1.5rem 0;
        gap: 1rem;
    }

    .divider-line {
        height: 1px;
        width: 80px;
        background: linear-gradient(90deg, transparent, var(--gold-primary), transparent);
    }

    .divider-icon {
        color: var(--gold-primary);
        font-size: 1.2rem;
    }

    /* Feature cards */
    .features-container {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin: 2rem 0;
        flex-wrap: wrap;
    }

    .feature-card {
        background: rgba(212, 168, 83, 0.08);
        border: 1px solid rgba(212, 168, 83, 0.2);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        flex: 1;
        min-width: 140px;
        max-width: 180px;
    }

    .feature-card:hover {
        transform: translateY(-5px);
        border-color: var(--gold-primary);
        box-shadow: 0 10px 30px rgba(212, 168, 83, 0.2);
    }

    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
    }

    .feature-text {
        font-family: 'Outfit', sans-serif;
        font-size: 0.85rem;
        color: var(--desert-sand);
        font-weight: 400;
    }

    /* Chat container */
    .chat-container {
        background: rgba(13, 19, 33, 0.6);
        border-radius: 24px;
        border: 1px solid rgba(212, 168, 83, 0.15);
        padding: 1.5rem;
        backdrop-filter: blur(20px);
        box-shadow: 
            0 4px 30px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(212, 168, 83, 0.1);
    }

    /* Chat messages */
    .stChatMessage {
        background: transparent !important;
        border-radius: 16px !important;
        margin-bottom: 1rem !important;
        padding: 1rem !important;
    }

    /* User message */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, rgba(212, 168, 83, 0.15) 0%, rgba(184, 115, 51, 0.1) 100%) !important;
        border: 1px solid rgba(212, 168, 83, 0.3) !important;
        margin-left: 2rem !important;
    }

    /* Assistant message */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: rgba(26, 43, 74, 0.5) !important;
        border: 1px solid rgba(212, 168, 83, 0.1) !important;
        margin-right: 2rem !important;
    }

    /* Message text - brighter and more visible */
    .stChatMessage p {
        font-family: 'Outfit', sans-serif !important;
        color: #FFFFFF !important;
        font-size: 1rem !important;
        line-height: 1.7 !important;
    }

    .stChatMessage {
        color: #FFFFFF !important;
    }

    /* Ensure all markdown text is white */
    .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: #FFFFFF !important;
    }

    /* Chat message content */
    [data-testid="stChatMessageContent"] {
        color: #FFFFFF !important;
    }

    [data-testid="stChatMessageContent"] p {
        color: #FFFFFF !important;
    }

    /* Chat input styling - complete override */
    .stChatInput {
        border-radius: 20px !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    .stChatInput > div {
        background: var(--midnight) !important;
        border: 2px solid rgba(212, 168, 83, 0.4) !important;
        border-radius: 20px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }

    .stChatInput > div:focus-within {
        border-color: var(--gold-primary) !important;
        box-shadow: 0 0 20px rgba(212, 168, 83, 0.3) !important;
    }

    .stChatInput textarea {
        font-family: 'Outfit', sans-serif !important;
        color: #FFFFFF !important;
        font-size: 1rem !important;
        background: transparent !important;
    }

    .stChatInput textarea::placeholder {
        color: rgba(245, 230, 211, 0.5) !important;
    }

    /* Force dark background on all chat input elements */
    [data-testid="stChatInput"] {
        background: var(--midnight) !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    [data-testid="stChatInput"] > div {
        background: var(--midnight) !important;
        width: 100% !important;
    }

    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: #FFFFFF !important;
    }

    /* Bottom container / chat input area - FULL WIDTH */
    .stChatFloatingInputContainer {
        background: var(--midnight) !important;
        padding: 1rem 2rem !important;
        max-width: 100% !important;
        width: 100% !important;
        left: 0 !important;
        right: 0 !important;
    }

    [data-testid="stBottom"] {
        background: var(--midnight) !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    [data-testid="stBottom"] > div {
        background: var(--midnight) !important;
        width: 100% !important;
        max-width: 100% !important;
        padding: 0 1rem !important;
    }

    [data-testid="stBottomBlockContainer"] {
        background: var(--midnight) !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    /* Override any white backgrounds in bottom area */
    .st-emotion-cache-1wbqy5l,
    .st-emotion-cache-nahz7x,
    .st-emotion-cache-1f3w014,
    .st-emotion-cache-1eo1tir,
    .st-emotion-cache-18ni7ap,
    .st-emotion-cache-dvne4q,
    .st-emotion-cache-12fmjuu {
        background: var(--midnight) !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    /* Chat input inner elements */
    .st-emotion-cache-1gulkj5,
    .st-emotion-cache-1f3w014 > div,
    .stChatInputContainer {
        background: var(--midnight) !important;
        border: 2px solid rgba(212, 168, 83, 0.4) !important;
        border-radius: 16px !important;
    }

    /* The actual input field inside */
    .st-emotion-cache-1gulkj5 textarea,
    .stChatInputContainer textarea,
    div[data-baseweb="textarea"] textarea {
        background: transparent !important;
        color: #FFFFFF !important;
        caret-color: var(--gold-primary) !important;
    }

    /* Input wrapper */
    div[data-baseweb="textarea"],
    div[data-baseweb="base-input"] {
        background: var(--midnight) !important;
        border-color: rgba(212, 168, 83, 0.4) !important;
    }

    /* Placeholder text */
    div[data-baseweb="textarea"] textarea::placeholder {
        color: rgba(212, 168, 83, 0.6) !important;
    }

    /* Spinner styling */
    .stSpinner > div {
        border-color: var(--gold-primary) !important;
    }

    /* Avatar styling */
    [data-testid="chatAvatarIcon-user"] {
        background: linear-gradient(135deg, var(--gold-primary), var(--copper)) !important;
    }

    [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, var(--deep-blue), #2A3B5A) !important;
        border: 2px solid var(--gold-primary) !important;
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--midnight);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--gold-dark);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--gold-primary);
    }

    /* Force dark theme everywhere */
    .main, .main > div, section[data-testid="stSidebar"],
    div[data-testid="stToolbar"], div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {
        background: transparent !important;
    }

    /* Override all possible white backgrounds */
    .element-container, .stTextInput > div, .stTextArea > div {
        background: transparent !important;
    }

    /* Global text color override */
    body, p, span, div, label, .stText {
        color: #FFFFFF !important;
    }

    /* Keep gold colors for specific elements */
    .hero-title, .feature-text, .hero-subtitle, .footer-text {
        color: inherit !important;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--gold-primary), var(--copper)) !important;
        color: var(--midnight) !important;
        border: none !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--gold-light), var(--gold-primary)) !important;
    }

    /* Footer decoration */
    .footer-decoration {
        text-align: center;
        margin-top: 2rem;
        padding: 1rem;
        opacity: 0.6;
    }

    .footer-text {
        font-family: 'Outfit', sans-serif;
        font-size: 0.8rem;
        color: var(--desert-sand);
        letter-spacing: 0.05em;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2rem;
        }
        .hero-subtitle {
            font-size: 0.9rem;
        }
        .feature-card {
            min-width: 100px;
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-section">
    <span class="hero-icon">🕌</span>
    <h1 class="hero-title">MENA Explorer</h1>
    <p class="hero-subtitle">Your Gateway to Ancient Wonders</p>
    <div class="divider">
        <span class="divider-line"></span>
        <span class="divider-icon">◆</span>
        <span class="divider-line"></span>
    </div>
</div>
""", unsafe_allow_html=True)

# Feature cards
st.markdown("""
<div class="features-container">
    <div class="feature-card">
        <span class="feature-icon">🏜️</span>
        <span class="feature-text">Desert Adventures</span>
    </div>
    <div class="feature-card">
        <span class="feature-icon">🏛️</span>
        <span class="feature-text">Ancient Ruins</span>
    </div>
    <div class="feature-card">
        <span class="feature-icon">🌊</span>
        <span class="feature-text">Coastal Escapes</span>
    </div>
    <div class="feature-card">
        <span class="feature-icon">🍽️</span>
        <span class="feature-text">Local Cuisine</span>
    </div>
</div>
""", unsafe_allow_html=True)


# Initialize the RAG agent
@st.cache_resource
def load_agent():
    return RAGAgent()


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask about destinations, culture, food, or travel tips..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get agent response with loading indicator
    with st.spinner("✨ Discovering insights..."):
        agent = load_agent()
        response = agent.ask(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown('</div>', unsafe_allow_html=True)

# Footer decoration
st.markdown("""
<div class="footer-decoration">
    <p class="footer-text">✦ Explore the magic of the Middle East & North Africa ✦</p>
</div>
""", unsafe_allow_html=True)