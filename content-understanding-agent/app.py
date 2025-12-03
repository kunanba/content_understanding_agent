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

# Custom CSS for professional UI
st.markdown("""
<style>
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #0284c7 0%, #1e40af 100%);
    }
    
    /* Main container */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0284c7 0%, #1e40af 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .header-title {
        font-size: 28px;
        font-weight: 600;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .status-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: #4ade80;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Panel styling */
    .stColumn {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Section headers */
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* File uploader styling */
    .uploadedFile {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s ease;
        border: none;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #1e40af 100%);
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(2, 132, 199, 0.4);
    }
    
    .stButton > button[kind="secondary"] {
        background: white;
        color: #0284c7;
        border: 1px solid #e2e8f0;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #f0f9ff;
        border-color: #0284c7;
    }
    
    /* Quick action buttons */
    .quick-action {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 13px;
        color: #475569;
    }
    
    .quick-action:hover {
        background: #f0f9ff;
        border-color: #0284c7;
        color: #0284c7;
        transform: translateX(4px);
    }
    
    /* Chat messages */
    .stChatMessage {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Stats cards */
    .stat-card {
        background: white;
        padding: 1.25rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #0284c7;
        margin-bottom: 4px;
    }
    
    .stat-label {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 8px;
        border: none;
    }
    
    /* Chat input */
    .stChatInputContainer {
        border-radius: 8px;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
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
                # Add to messages and process
                clean_question = question.split(" ", 1)[1]  # Remove emoji
                st.session_state.messages.append({"role": "user", "content": clean_question})
                
                if st.session_state.agent and st.session_state.thread_id:
                    try:
                        response = st.session_state.agent.query(clean_question, st.session_state.thread_id)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        st.markdown("---")
        
        # Chat input at the bottom
        if prompt := st.chat_input("Ask a question about your document..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get agent response
            if st.session_state.agent and st.session_state.thread_id:
                try:
                    response = st.session_state.agent.query(prompt, st.session_state.thread_id)
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
