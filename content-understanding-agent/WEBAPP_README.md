# Content Understanding Agent - Streamlit Web App

A beautiful web interface for the Content Understanding Agent that allows you to:
- 📤 Upload documents to Azure Blob Storage
- 🤖 Process documents with AI-powered OCR and data extraction
- 💬 Chat with the agent to query extracted data
- 📊 View processing results and validation reports

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements-web.txt
   ```

2. **Configure environment:**
   - Make sure your `.env` file has all the required settings
   - Ensure you're logged into Azure CLI: `az login`

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Access the app:**
   - Open your browser to `http://localhost:8501`

## Features

### 📤 Upload & Process
- Drag & drop or browse to upload documents (PNG, JPG, PDF)
- Automatic upload to Azure Blob Storage incoming-docs container
- One-click document processing with full validation

### 💬 Natural Language Chat
- Ask questions about your processed documents
- Get detailed answers about personal details, dates, form types, etc.
- Quick question buttons for common queries
- Persistent chat history within session

### 🤖 AI Agent Integration
- Uses Microsoft Agent Framework
- Orchestrates OCR → Parse → Validate → Excel → Cleanup workflow
- Real-time validation of data extraction quality
- Error handling and status reporting

## Deployment Options

### Azure Web Apps
1. Create Azure Web App (Python 3.10)
2. Configure environment variables in Azure Portal
3. Deploy using:
   ```bash
   az webapp up --name content-understanding-app --resource-group demo-ak
   ```

### Streamlit Cloud
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Add secrets in Streamlit dashboard
4. Deploy with one click

## Usage Tips

1. **Processing Documents:**
   - Upload supported formats (PNG, JPG, PDF)
   - Wait for upload confirmation before processing
   - Processing takes 30-60 seconds per document

2. **Asking Questions:**
   - Be specific in your queries
   - Use quick question buttons for common needs
   - The agent remembers context within the session

3. **Troubleshooting:**
   - If agent initialization fails, check `.env` configuration
   - If upload fails, verify Azure CLI login: `az account show`
   - Clear chat to start fresh conversation

## Architecture

```
User Browser
    ↓
Streamlit Web App (app.py)
    ↓
ContentUnderstandingAgent (agent.py)
    ↓
Azure Functions (Function App)
    ├─ perform_ocr
    ├─ parse_ocr
    ├─ create_excel
    └─ clean_up
    ↓
Azure Services
    ├─ Blob Storage
    ├─ Content Understanding
    └─ AI Foundry (Agent Framework)
```
