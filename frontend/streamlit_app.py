import streamlit as st
import requests
from datetime import datetime
from typing import Optional, Dict, List
import time
import json

#configurations
API_URL = "http://backend:8000"
REQUEST_TIMEOUT = 30

st.set_page_config(
    page_title="Brain Box",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        padding: 1rem 2rem;
    }
    
    .chat-message {
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
        margin-right: 0;
        max-width: 70%;
    }
    
    .bot-message {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
        color: white;
        margin-left: 0;
        margin-right: auto;
        max-width: 70%;
    }
    
    .chat-container {
        max-height: 60vh;
        overflow-y: auto;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .chat-wrapper {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    
    .message-header {
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .message-content {
        font-size: 1.05rem;
        line-height: 1.7;
        margin: 0.8rem 0;
        white-space: pre-wrap;
    }
    
    .timestamp {
        font-size: 0.75rem;
        opacity: 0.85;
        margin-top: 0.8rem;
        font-style: italic;
    }
    
    .source-box {
        background-color: #fff8e1;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #ffa726;
        color: #333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        font-size: 0.9rem;
    }
    
    .source-header {
        font-weight: 700;
        color: #e65100;
        margin-bottom: 0.3rem;
        font-size: 0.9rem;
    }
    
    .bot-message .message-header {
        color: #667eea;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .welcome-container {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 1.5rem;
        margin: 2rem 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .welcome-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .welcome-subtitle {
        font-size: 1.3rem;
        opacity: 0.95;
        margin-bottom: 2rem;
    }
    
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #667eea;
        padding: 12px 20px;
        font-size: 1rem;
    }
    
    .stButton > button {
        border-radius: 25px;
        font-weight: 600;
        padding: 0.5rem 2rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Footer styling to position below chat input */
    .footer-below-input {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        z-index: 999999;
        padding: 0.5rem;
        text-align: center;
        border-top: 1px solid #e0e0e0;
    }
    
    /* Add padding to main content to prevent overlap */
    section[data-testid="stChatInput"] {
        margin-bottom: 3rem !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'message_count' not in st.session_state:
    st.session_state.message_count = 0

if 'api_status' not in st.session_state:
    st.session_state.api_status = False

if 'show_sources' not in st.session_state:
    st.session_state.show_sources = True

if 'show_timestamps' not in st.session_state:
    st.session_state.show_timestamps = True

if 'session_id' not in st.session_state:
    st.session_state.session_id = f"user_{int(time.time())}"

if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None

def check_api_health() -> bool:
    """Check if API is running and healthy"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('bot_loaded', False)
        return False
    except requests.exceptions.RequestException:
        return False

def send_question(question: str) -> Optional[Dict]:
    """Send question to API and get response"""
    try:
        payload = {
            "question": question,
            "session_id": st.session_state.session_id
        }
        
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            st.error("🔧 Bot is initializing. Please wait a moment and try again.")
            return None
        elif response.status_code == 400:
            st.error("❌ Invalid question. Please try again.")
            return None
        else:
            st.error(f"❌ API Error: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to API. Please ensure the backend is running.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def format_timestamp() -> str:
    """Get formatted timestamp"""
    return datetime.now().strftime("%I:%M %p")

def export_chat_history() -> str:
    """Export chat history as formatted text"""
    if not st.session_state.chat_history:
        return "No chat history available."
    
    export_text = "=" * 70 + "\n"
    export_text += "RAG BOT CHAT HISTORY\n"
    export_text += f"Session ID: {st.session_state.session_id}\n"
    export_text += f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    export_text += "=" * 70 + "\n\n"
    
    for idx, message in enumerate(st.session_state.chat_history, 1):
        role = "USER" if message['role'] == 'user' else "ASSISTANT"
        timestamp = message.get('timestamp', 'N/A')
        
        export_text += f"[{idx}] {role} ({timestamp}):\n"
        export_text += f"{message['content']}\n"
        
        if 'sources' in message and message['sources']:
            export_text += f"\nSources ({len(message['sources'])}):\n"
            for sidx, source in enumerate(message['sources'], 1):
                export_text += f"  {sidx}. {source}\n"
        
        export_text += "\n" + "-" * 70 + "\n\n"
    
    return export_text

def clear_chat():
    """Clear chat history"""
    st.session_state.chat_history = []
    st.session_state.message_count = 0

def get_api_stats() -> Optional[Dict]:
    """Get API statistics"""
    try:
        response = requests.get(f"{API_URL}/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def upload_document(file) -> Dict:
    """Upload a document to the backend"""
    try:
        files = {'file': (file.name, file.getvalue(), file.type)}
        response = requests.post(
            f"{API_URL}/upload",
            files=files,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return {'success': True, 'message': response.json().get('message', 'Upload successful')}
        else:
            return {'success': False, 'message': f"Upload failed: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': "Cannot connect to API. Please ensure the backend is running."}
    except Exception as e:
        return {'success': False, 'message': f"Error: {str(e)}"}

def reload_documents() -> Dict:
    """Reload all documents from data folder"""
    try:
        response = requests.post(
            f"{API_URL}/reload",
            timeout=60  # Longer timeout for processing
        )
        
        if response.status_code == 200:
            return {'success': True, 'message': response.json().get('message', 'Documents reloaded')}
        else:
            return {'success': False, 'message': f"Reload failed: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': "Cannot connect to API. Please ensure the backend is running."}
    except Exception as e:
        return {'success': False, 'message': f"Error: {str(e)}"}

with st.sidebar:
    # Header
    st.markdown("""
        <div style='text-align: center; padding: 0.0005rem 0;'>
            <h1 style='color: #667eea; margin: 0;'>Brain Box</h1>
            <p style='color: #666; margin: 0.0005rem 0;'>Intelligent Document Assistant</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Document Upload Section
    st.subheader("📤 Upload Documents")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'txt', 'docx', 'doc', 'csv', 'xlsx', 'xls', 'json', 'md'],
        help="Upload documents to add to the knowledge base",
        key="main_uploader",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # Create a unique identifier for this file
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        
        # Only upload if it's a different file from the last one
        if st.session_state.last_uploaded_file != file_id:
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                result = upload_document(uploaded_file)
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                    st.session_state.last_uploaded_file = file_id
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")
                    time.sleep(2)
    
    st.markdown("---")
    
    # API Status Check
    api_status = check_api_health()
    st.session_state.api_status = api_status
    
    if api_status:
        st.markdown("""
            <div style='background: #e8f5e9; padding: 1rem; border-radius: 0.5rem; 
                        border-left: 4px solid #4caf50; margin-bottom: 1rem;'>
                <span style='color: #2e7d32; font-weight: 600;'>✅ API Connected</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style='background: #ffebee; padding: 1rem; border-radius: 0.5rem; 
                        border-left: 4px solid #f44336; margin-bottom: 1rem;'>
                <span style='color: #c62828; font-weight: 600;'>❌ API Disconnected</span>
            </div>
        """, unsafe_allow_html=True)
        st.warning(f"⚠️ Please start the backend server:\n```bash\ncd backend\npython app.py\n```")
    
    st.markdown("---")
    
    # Display Settings
    st.subheader("⚙️ Display Settings")
    
    st.session_state.show_sources = st.checkbox(
        "📚 Show Sources",
        value=st.session_state.show_sources,
        help="Display source documents for each answer"
    )
    
    st.session_state.show_timestamps = st.checkbox(
        "⏰ Show Timestamps",
        value=st.session_state.show_timestamps,
        help="Display timestamp for each message"
    )
    st.markdown("---")
    
    # Actions
    st.subheader("🔧 Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear", use_container_width=True, type="secondary"):
            clear_chat()
            st.rerun()
    
    with col2:
        if st.session_state.chat_history:
            chat_export = export_chat_history()
            st.download_button(
                label="💾 Export",
                data=chat_export,
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
                type="primary"
            )
        else:
            st.button("💾 Export", use_container_width=True, disabled=True)
    
    st.markdown("---")
    
    # Session Info
    with st.expander("🔐 Session Info"):
        st.code(f"Session ID: {st.session_state.session_id}")
        st.caption(f"Started: {datetime.now().strftime('%Y-%m-%d')}")
        
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.session_id = f"user_{int(time.time())}"
            clear_chat()
            st.rerun()
    
    # About
    with st.expander("ℹ️ About"):
        st.markdown("""
        **Brain Box v1.0**
        
        This chatbot uses **Retrieval-Augmented Generation (RAG)** to:
        - Search through your document database
        - Provide accurate, sourced answers
        - Maintain conversation context
        - Reference original sources
        """)

# Page Header - At the very top
st.markdown("""
    <div style='text-align: center; padding: 1rem 0 0.5rem 0;'>
        <h1 style='color: #667eea; margin: 0; font-size: 2.5rem; font-weight: 700;'>Welcome to Brain Box 🧠</h1>
    </div>
""", unsafe_allow_html=True)

# Chat History Container
if st.session_state.chat_history:
    for idx, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message['role']):
            st.write(message['content'])
            
            # Show timestamp if enabled
            if st.session_state.show_timestamps and 'timestamp' in message:
                st.caption(f"⏰ {message['timestamp']}")
            
            # Display sources for assistant messages
            if message['role'] == 'assistant' and st.session_state.show_sources and 'sources' in message and message['sources']:
                with st.expander(f"📚 View {len(message['sources'])} Source(s)", expanded=False):
                    for source_idx, source in enumerate(message['sources'], 1):
                        st.text(f"Source {source_idx}:")
                        st.text(source)
                        st.divider()

user_input = st.chat_input("💭 Type your question here...", key="chat_input_box")

if user_input:
    if not st.session_state.api_status:
        st.error("❌ API is not connected. Please start the backend server.")
        st.info("""
        **To start the backend:**
        ```bash
        cd backend
        python app.py
        ```
        """)
    else:
        # Add user message to chat history
        timestamp = format_timestamp()
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': timestamp
        })
        st.session_state.message_count += 1
        
        # Get bot response with loading indicator
        with st.spinner('🤔 Thinking...'):
            try:
                result = send_question(user_input)
                
                if result:
                    # Extract answer and sources
                    answer = result.get('answer', 'Sorry, I could not generate an answer.')
                    sources = result.get('sources', [])
                    
                    # Add bot response to chat history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': answer,
                        'sources': sources,
                        'timestamp': format_timestamp()
                    })
                    st.session_state.message_count += 1
                    
                    # Success message
                    st.success("✅ Answer generated!")
                else:
                    # Add error message to chat
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': "Sorry, I encountered an error processing your question. Please try again.",
                        'timestamp': format_timestamp()
                    })
                    st.session_state.message_count += 1
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"Error: {str(e)}",
                    'timestamp': format_timestamp()
                })
                st.session_state.message_count += 1
        
        # Rerun to update the chat display
        st.rerun()


st.markdown("""
    <div class='footer-below-input'>
        <p style='margin: 0; color: #666; font-size: 0.85rem;'>🚀 Brain Box v1.0 | Built with ❤️</p>
    </div>
""", unsafe_allow_html=True)


st.markdown("""
    <script>
    const doc = window.parent.document;
    const inputs = doc.querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const submitBtn = doc.querySelector('button[kind="primary"]');
                if (submitBtn) submitBtn.click();
            }
        });
    });
    </script>
""", unsafe_allow_html=True)