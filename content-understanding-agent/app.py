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

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Content Understanding Agent",
    page_icon="📄",
    layout="wide"
)

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
            with st.spinner("🤖 Initializing AI Agent..."):
                st.session_state.agent = ContentUnderstandingAgent()
            return True, "✅ Agent initialized successfully"
        except Exception as e:
            return False, f"❌ Failed to initialize agent: {str(e)}"
    return True, "Agent already initialized"


# Header
st.title("📄 Content Understanding Agent")
st.markdown("**Upload documents, process with AI, and query extracted data using natural language**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Check environment variables
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    storage_account = os.getenv("STORAGE_ACCOUNT_NAME", "demostorageak")
    
    if project_endpoint:
        st.success("✅ Azure AI Foundry configured")
    else:
        st.error("❌ PROJECT_ENDPOINT not configured")
    
    st.info(f"📦 Storage: {storage_account}")
    
    st.divider()
    
    st.header("📋 How to Use")
    st.markdown("""
    1. **Upload** a document (PNG, JPG, PDF)
    2. **Process** it to extract data
    3. **Ask questions** about the content
    4. View results and insights
    """)
    
    st.divider()
    
    # Initialize agent button
    if st.button("🔄 Initialize Agent"):
        success, message = initialize_agent()
        if success:
            st.success(message)
        else:
            st.error(message)

# Main content area - 2 columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📤 Upload & Process")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a document to process",
        type=["png", "jpg", "jpeg", "pdf"],
        help="Upload a document for OCR and data extraction"
    )
    
    if uploaded_file:
        st.success(f"📄 File selected: **{uploaded_file.name}**")
        
        # Show file preview for images
        if uploaded_file.type.startswith('image/'):
            st.image(uploaded_file, caption=uploaded_file.name)
        
        # Upload and process buttons
        col_upload, col_process = st.columns(2)
        
        with col_upload:
            if st.button("📤 Upload to Storage"):
                with st.spinner("Uploading..."):
                    success, message = upload_to_blob(uploaded_file.getvalue(), uploaded_file.name)
                    if success:
                        st.success(message)
                        st.session_state.last_uploaded_file = uploaded_file.name
                    else:
                        st.error(message)
        
        with col_process:
            if st.button("▶️ Process Document", type="primary"):
                # Initialize agent if needed
                if st.session_state.agent is None:
                    success, message = initialize_agent()
                    if not success:
                        st.error(message)
                        st.stop()
                
                # Upload file first if not already uploaded
                if not hasattr(st.session_state, 'last_uploaded_file') or st.session_state.last_uploaded_file != uploaded_file.name:
                    with st.spinner("Uploading file..."):
                        success, message = upload_to_blob(uploaded_file.getvalue(), uploaded_file.name)
                        if not success:
                            st.error(message)
                            st.stop()
                        st.session_state.last_uploaded_file = uploaded_file.name
                
                # Process with agent
                st.session_state.processing = True
                with st.spinner("🤖 Processing document... This may take a minute..."):
                    try:
                        result = st.session_state.agent.process_document(uploaded_file.name)
                        
                        if result["success"]:
                            st.session_state.thread_id = result["thread_id"]
                            st.session_state.last_processed_file = uploaded_file.name
                            
                            # Display results
                            st.success("✅ Document processed successfully!")
                            
                            with st.expander("📊 Processing Results", expanded=True):
                                for i, response in enumerate(result["responses"], 1):
                                    st.markdown(f"**Step {i} Results:**")
                                    st.info(response)
                                    st.divider()
                        else:
                            st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                    finally:
                        st.session_state.processing = False
    
    else:
        st.info("👆 Upload a document to get started")

with col2:
    st.header("💬 Chat with Agent")
    
    # Chat interface
    if st.session_state.last_processed_file:
        st.success(f"📄 Active document: **{st.session_state.last_processed_file}**")
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about the document..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get agent response
            if st.session_state.agent and st.session_state.thread_id:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            response = st.session_state.agent.query(prompt, st.session_state.thread_id)
                            st.markdown(response)
                            
                            # Add assistant message
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        except Exception as e:
                            error_msg = f"❌ Error: {str(e)}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                st.error("❌ Agent not initialized or no active thread")
        
        # Quick action buttons
        st.divider()
        st.markdown("**💡 Quick Questions:**")
        
        quick_questions = [
            "What personal details are in this document?",
            "What type of document is this?",
            "Extract all names and addresses",
            "Are there any dates mentioned?",
            "Summarize the key information"
        ]
        
        cols = st.columns(2)
        for i, question in enumerate(quick_questions):
            with cols[i % 2]:
                if st.button(question, key=f"quick_{i}"):
                    # Add to messages and process
                    st.session_state.messages.append({"role": "user", "content": question})
                    
                    if st.session_state.agent and st.session_state.thread_id:
                        try:
                            response = st.session_state.agent.query(question, st.session_state.thread_id)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    else:
        st.info("👈 Process a document first to start chatting")
        
        st.markdown("""
        ### What can you ask?
        
        After processing a document, you can ask questions like:
        - "What are the personal details in this document?"
        - "Extract all names and phone numbers"
        - "What is this form about?"
        - "Are there any dates mentioned?"
        - "Summarize the plaintiff information"
        - Any other natural language question about the content!
        """)

# Footer
st.divider()
st.caption("🤖 Powered by Microsoft Agent Framework & Azure AI")
