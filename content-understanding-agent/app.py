"""
Streamlit Web App for Content Understanding Agent
Upload documents, process them with AI, and query the extracted data.
"""
import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from agent import ContentUnderstandingAgent
import time
from datetime import datetime

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Content Understanding Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Microsoft Azure design
st.markdown("""
<style>
    /* Import Segoe UI font (Microsoft's standard) */
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
    
    /* Main background - Azure Portal style */
    .stApp {
        background: #f5f5f5;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main container */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Header styling - Azure Portal header */
    .main-header {
        background: #0078d4;
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 4px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .header-title {
        font-size: 24px;
        font-weight: 600;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
        letter-spacing: -0.5px;
    }
    
    .status-badge {
        background: rgba(255, 255, 255, 0.15);
        padding: 6px 14px;
        border-radius: 2px;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 8px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: #00c851;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Panel styling - Azure card style */
    .stColumn {
        background: white;
        padding: 1.5rem;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Section headers */
    .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #323130;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #0078d4;
    }
    
    /* File uploader styling */
    .uploadedFile {
        background: white;
        border: 1px solid #d1d1d1;
        border-radius: 2px;
        padding: 12px;
    }
    
    /* Button styling - Azure Fluent Design */
    .stButton > button {
        border-radius: 2px;
        font-weight: 600;
        padding: 8px 16px;
        transition: all 0.1s ease;
        border: 1px solid transparent;
        font-size: 14px;
    }
    
    .stButton > button[kind="primary"] {
        background: #0078d4;
        color: white;
        border-color: #0078d4;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #106ebe;
        border-color: #106ebe;
    }
    
    .stButton > button[kind="secondary"] {
        background: white;
        color: #323130;
        border: 1px solid #8a8886;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #f3f2f1;
        border-color: #323130;
    }
    
    /* Quick action buttons - Azure style */
    .quick-action {
        background: white;
        border: 1px solid #d1d1d1;
        border-radius: 2px;
        padding: 10px 14px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.1s ease;
        font-size: 14px;
        font-size: 13px;
        color: #475569;
    }
    
    .quick-action:hover {
        background: #f3f2f1;
        border-color: #0078d4;
    }
    
    /* Chat messages - Azure style */
    .stChatMessage {
        background: white;
        border-radius: 2px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 3px solid #0078d4;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    /* Stats cards - Azure metrics style */
    .stat-card {
        background: white;
        padding: 16px;
        border-radius: 2px;
        border: 1px solid #d1d1d1;
        text-align: center;
    }
    
    .stat-value {
        font-size: 32px;
        font-weight: 600;
        color: #0078d4;
        margin-bottom: 4px;
    }
    
    .stat-label {
        font-size: 13px;
        color: #605e5c;
        font-weight: 400;
    }
    
    /* Info boxes - Azure alert style */
    .stAlert {
        border-radius: 2px;
        border-left: 4px solid #0078d4;
    }
    
    /* Success boxes */
    .stSuccess {
        border-left-color: #00c851;
    }
    
    /* Warning boxes */
    .stWarning {
        border-left-color: #ffb900;
    }
    
    /* Error boxes */
    .stError {
        border-left-color: #e81123;
    }
    
    /* Chat input */
    .stChatInputContainer {
        border-radius: 2px;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Processing indicator - Azure style */
    .processing-banner {
        background: #fff4ce;
        border: 1px solid #ffb900;
        border-left: 4px solid #ffb900;
        border-radius: 2px;
        padding: 12px 16px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 14px;
        color: #323130;
    }
    /* Processing indicator */
    .processing-banner {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 13px;
        color: #ea580c;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'last_processed_file' not in st.session_state:
    st.session_state.last_processed_file = None
if 'documents_processed' not in st.session_state:
    st.session_state.documents_processed = 0
if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False
if 'query_cache' not in st.session_state:
    st.session_state.query_cache = {}  # Cache responses to avoid duplicate API calls
if 'last_query_time' not in st.session_state:
    st.session_state.last_query_time = 0  # Track last query timestamp for rate limiting
if 'pending_question' not in st.session_state:
    st.session_state.pending_question = None  # Track pending quick question to process


def upload_to_blob(file_data, filename):
    """Upload file to Azure Blob Storage incoming-docs container."""
    try:
        storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME", "demostorageak")
        account_url = f"https://{storage_account_name}.blob.core.windows.net"
        
        # Try DefaultAzureCredential first
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=credential
        )
        
        container_client = blob_service_client.get_container_client("incoming-docs")
        blob_client = container_client.get_blob_client(filename)
        
        # Upload file
        blob_client.upload_blob(file_data, overwrite=True)
        return True, f"✅ Uploaded {filename} to incoming-docs"
    except Exception as e:
        error_msg = str(e)
        if "AuthorizationFailure" in error_msg:
            return False, f"❌ Permission denied. Your Azure account needs 'Storage Blob Data Contributor' role. Role was just assigned - please wait 2-5 minutes for it to propagate, then try again."
        return False, f"❌ Upload failed: {error_msg}"


def initialize_agent():
    """Initialize the Content Understanding Agent."""
    if st.session_state.agent is None:
        try:
            st.session_state.agent = ContentUnderstandingAgent()
            st.session_state.agent_initialized = True
            return True, "✅ Agent initialized successfully"
        except Exception as e:
            return False, f"❌ Failed to initialize agent: {str(e)}"
    return True, "Agent already initialized"


def query_with_cache(question: str, thread_id: str, max_retries: int = 3):
    """Query agent with caching and retry logic to handle rate limits."""
    import time
    import re
    
    # Create cache key from question and thread
    cache_key = f"{thread_id}:{question.lower().strip()}"
    
    # Check cache first
    if cache_key in st.session_state.query_cache:
        return st.session_state.query_cache[cache_key]
    
    # Make actual API call with retry logic
    for attempt in range(max_retries):
        try:
            response = st.session_state.agent.query(question, thread_id)
            
            # Store in cache on success
            st.session_state.query_cache[cache_key] = response
            return response
            
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error
            if 'rate_limit_exceeded' in error_str or 'RateLimitError' in error_str:
                # Try to extract wait time from error message
                wait_match = re.search(r'retry after (\d+) seconds', error_str)
                wait_time = int(wait_match.group(1)) if wait_match else (2 ** attempt) * 5
                
                if attempt < max_retries - 1:
                    st.warning(f"⏳ Rate limit hit. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    return f"❌ **Rate Limit Exceeded**\n\nThe AI model is receiving too many requests. Please:\n- Wait 30-60 seconds before asking another question\n- Request quota increase at: https://aka.ms/oai/quotaincrease\n\nTechnical details: {error_str}"
            else:
                # Non-rate-limit error, raise it
                raise
    
    return "❌ Failed to get response after multiple retries."


# Custom header with status badge
agent_status = "Agent Active" if st.session_state.agent_initialized else "Agent Inactive"
st.markdown(f"""
<div class="main-header">
    <h1 class="header-title">
        <span>🤖</span>
        Content Understanding Agent
    </h1>
    <div class="status-badge">
        <div class="status-dot"></div>
        {agent_status}
    </div>
</div>
""", unsafe_allow_html=True)

# Auto-initialize agent on first load
if not st.session_state.agent_initialized:
    success, message = initialize_agent()
    if success:
        st.rerun()

# Main content area - 2 columns
col1, col2 = st.columns([1, 1.5], gap="large")

with col1:
    st.markdown('<div class="section-title">📤 Upload Document</div>', unsafe_allow_html=True)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a document to process",
        type=["png", "jpg", "jpeg", "pdf"],
        help="Upload a document for OCR and data extraction"
    )
    
    if uploaded_file:
        # File info card
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.markdown(f"""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 20px; display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; background: #dbeafe; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">
                📋
            </div>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: #1e293b; margin-bottom: 4px;">{uploaded_file.name}</div>
                <div style="font-size: 12px; color: #64748b;">{file_size_mb:.2f} MB • Just uploaded</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Process button
        if st.button("⚡ Process Document", type="primary", use_container_width=True):
            # Initialize agent if needed
            if st.session_state.agent is None:
                success, message = initialize_agent()
                if not success:
                    st.error(message)
                    st.stop()
            
            # Upload file first
            with st.spinner("Uploading file..."):
                success, message = upload_to_blob(uploaded_file.getvalue(), uploaded_file.name)
                st.info(message)  # Show upload status
                if not success:
                    st.error(message)
                    st.stop()
            
            # Process with agent
            if st.session_state.processing:
                st.markdown('<div class="processing-banner">⚡ Processing document: OCR extraction in progress...</div>', unsafe_allow_html=True)
            
            st.session_state.processing = True
            with st.spinner("🤖 Processing document... This may take a minute..."):
                try:
                    result = st.session_state.agent.process_document(uploaded_file.name)
                    
                    if result["success"]:
                        st.session_state.thread_id = result["thread_id"]
                        st.session_state.last_processed_file = uploaded_file.name
                        st.session_state.documents_processed += 1
                        
                        # Display results
                        st.success("✅ Document processed successfully!")
                        
                        # Add initial message to chat
                        initial_msg = "Hello! I've successfully processed your document. I extracted OCR data, parsed the content, and created an Excel summary. What would you like to know?"
                        if not any(msg["content"] == initial_msg for msg in st.session_state.messages):
                            st.session_state.messages.append({"role": "assistant", "content": initial_msg})
                        
                        with st.expander("📊 View Processing Details"):
                            for i, response in enumerate(result["responses"], 1):
                                st.markdown(f"**Step {i}:**")
                                st.info(response)
                    else:
                        st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    st.session_state.processing = False
        
        # Clear button
        if st.button("🗑️ Clear & Upload New", use_container_width=True):
            st.session_state.last_processed_file = None
            st.session_state.messages = []
            st.rerun()
    
    else:
        st.info("👆 Upload a document to get started")
    
    # Stats dashboard
    st.markdown("---")
    stat_col1, stat_col2 = st.columns(2)
    
    with stat_col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.documents_processed}</div>
            <div class="stat-label">Documents Processed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">7</div>
            <div class="stat-label">Functions Available</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-title">💬 Chat with Agent</div>', unsafe_allow_html=True)
    
    # Processing indicator
    if st.session_state.processing:
        st.markdown('<div class="processing-banner">⚡ Processing document: OCR extraction in progress...</div>', unsafe_allow_html=True)
    
    # Chat interface
    if st.session_state.last_processed_file:
        st.success(f"📄 Active document: **{st.session_state.last_processed_file}**")
        
        # Display chat messages in container
        chat_container = st.container(height=400)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                    st.markdown(message["content"])
        
        # Quick action buttons BEFORE chat input
        st.markdown("---")
        st.markdown("**⚡ Quick Questions:**")
        
        quick_questions = [
            "📊 What information did you extract?",
            "👤 Who is the patient in this claim?",
            "🏥 What medical services were provided?",
            "💰 Show me the claim amount breakdown",
            "✅ Validate the OCR results"
        ]
        
        # Display quick buttons in a compact grid
        for question in quick_questions:
            if st.button(question, key=f"quick_{question}", use_container_width=True):
                # Add user message and trigger immediate rerun to show it
                st.session_state.messages.append({"role": "user", "content": question})
                # Mark that we need to process this question
                st.session_state.pending_question = question
                st.rerun()
        
        # Process pending question after UI has updated
        if hasattr(st.session_state, 'pending_question') and st.session_state.pending_question:
            question_to_process = st.session_state.pending_question
            st.session_state.pending_question = None  # Clear the pending state
            
            if st.session_state.agent and st.session_state.thread_id:
                try:
                    # Extract clean question without emoji for API call
                    clean_question = question_to_process.split(" ", 1)[1] if " " in question_to_process else question_to_process
                    st.session_state.last_query_time = time.time()
                    response = query_with_cache(clean_question, st.session_state.thread_id)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
                    st.rerun()
        
        st.markdown("---")
        
        # Chat input at the bottom
        if prompt := st.chat_input("Ask a question about your document..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get agent response
            if st.session_state.agent and st.session_state.thread_id:
                try:
                    st.session_state.last_query_time = time.time()  # Update query timestamp
                    response = query_with_cache(prompt, st.session_state.thread_id)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.rerun()
            else:
                st.error("❌ Agent not initialized or no active thread")
    
    else:
        # Empty state
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; color: #94a3b8;">
            <div style="font-size: 64px; margin-bottom: 16px; opacity: 0.5;">💬</div>
            <div style="font-size: 16px; margin-bottom: 8px;">No active document</div>
            <div style="font-size: 13px;">Process a document to start chatting with the agent</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💡 What can you ask?")
        st.markdown("""
        After processing a document, you can ask questions like:
        - "Who is the patient in this insurance claim?"
        - "What medical services were provided?"
        - "Show me the claim amount breakdown"
        - "Extract all dates and amounts"
        - "Validate the OCR quality"
        - Any other natural language question about the content!
        """)
