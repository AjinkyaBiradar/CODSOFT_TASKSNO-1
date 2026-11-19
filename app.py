"""
Streamlit Chatbot Web Application
=================================
A modern conversational web interface for the rule-based chatbot.
Features:
- Conversational chat UI using st.chat_message
- Chat history persistence using st.session_state
- Dynamic user name memory across chat turns
- Sidebar with user profile, suggested prompts, and clear chat option
"""

import streamlit as st
from src.chatbot import RuleBasedChatbot

# Page configuration
st.set_page_config(
    page_title="Rule-Based Chatbot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom styling for a polished look
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .user-badge {
        background-color: #2e7d32;
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# Session State Initialization
# ==========================================
if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Hello! I am **RuleBot**, your rule-based assistant. What's your name, or how can I help you today?",
            "intent": "greeting",
            "score": 1.0
        }
    ]

# Initialize or update chatbot instance with current user_name
chatbot = RuleBasedChatbot(intents_path="data/intents.json", user_name=st.session_state.user_name)


# ==========================================
# Sidebar Controls & Information
# ==========================================
with st.sidebar:
    st.title("🤖 RuleBot Settings")
    st.markdown("A lightweight **rule-based chatbot** powered by regex patterns and keyword overlap matching.")
    
    st.divider()
    
    # User session identity status
    st.subheader("👤 User Session")
    if st.session_state.user_name:
        st.success(f"Remembered Name: **{st.session_state.user_name}**")
        if st.button("Forget / Reset Name", use_container_width=True):
            st.session_state.user_name = None
            chatbot.user_name = None
            st.rerun()
    else:
        st.info("Name not detected yet.\nTry typing: *'My name is [Name]'*")

    st.divider()

    # Suggested Prompts
    st.subheader("💡 Try Asking:")
    sample_prompts = [
        "My name is Jordan",
        "What is your name?",
        "What time is it?",
        "Tell me a joke",
        "What can you do?",
        "What day is it today?",
        "Can you help me?"
    ]

    selected_prompt = None
    for prompt in sample_prompts:
        if st.button(prompt, use_container_width=True):
            selected_prompt = prompt

    st.divider()

    # Option to clear chat history
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"Chat reset! Hello {st.session_state.user_name if st.session_state.user_name else ''}! How can I help you?",
                "intent": "greeting",
                "score": 1.0
            }
        ]
        st.rerun()


# ==========================================
# Main Chat Interface
# ==========================================
st.title("💬 Rule-Based Chatbot")
st.caption("Powered by Regex Matching, Keyword-Overlap Scoring, and Streamlit")

# Render previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Display small debug badge for matched intent if available
        if message["role"] == "assistant" and "intent" in message:
            tag = message.get("intent", "")
            score = message.get("score", 0.0)
            st.caption(f"Matched Intent: `{tag}` (confidence: {score})")

# Handle input from user (either text input or sidebar sample button click)
user_prompt = st.chat_input("Type your message here...") or selected_prompt

if user_prompt:
    # 1. Display user message in chat
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Save user message to session history
    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt
    })

    # 2. Get bot response using chatbot engine
    bot_result = chatbot.get_response(user_prompt)
    reply_text = bot_result["response"]
    matched_intent = bot_result["intent"]
    confidence_score = bot_result["score"]

    # Sync any newly discovered user name with session state
    if bot_result["user_name"] and bot_result["user_name"] != st.session_state.user_name:
        st.session_state.user_name = bot_result["user_name"]

    # 3. Display assistant message in chat
    with st.chat_message("assistant"):
        st.markdown(reply_text)
        st.caption(f"Matched Intent: `{matched_intent}` (confidence: {confidence_score})")

    # Save assistant message to session history
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply_text,
        "intent": matched_intent,
        "score": confidence_score
    })

    # Rerun if a sidebar prompt button was clicked to reset button state
    if selected_prompt:
        st.rerun()
