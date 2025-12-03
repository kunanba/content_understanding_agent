# Content Understanding Agent

AI-powered document processing system that orchestrates OCR, data extraction, validation, and natural language queries using Azure Functions and Microsoft Agent Framework.

## 🏗️ Architecture

```
User → Streamlit Web App → Content Understanding Agent → Azure Functions → Azure Services
                                                         ├─ perform_ocr
                                                         ├─ parse_ocr
                                                         ├─ create_excel
                                                         └─ clean_up
```

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Azure CLI installed and logged in (`az login`)
- Azure subscription with appropriate permissions

### 1. Deploy Azure Functions

**Create your Azure Resource Group:**

```bash
# Login to Azure
az login

# Set variables (customize these for your deployment)
RESOURCE_GROUP="your-resource-group-name"
LOCATION="eastus"  # or your preferred region
FUNCTION_APP_NAME="func-content-understanding-<your-unique-suffix>"
STORAGE_ACCOUNT="storage<your-unique-suffix>"  # must be lowercase, no hyphens

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION
```

**Deploy Infrastructure and Functions:**

Navigate to the `demo-azure-functions` directory and deploy using Bicep:

```bash
cd demo-azure-functions

# Deploy infrastructure (this creates all Azure resources)
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file deploy-function.bicep \
  --parameters functionAppName=$FUNCTION_APP_NAME \
               storageAccountName=$STORAGE_ACCOUNT \
               location=$LOCATION

# Deploy function code
func azure functionapp publish $FUNCTION_APP_NAME
```

**Required Azure Resources (created by Bicep):**
- Azure Function App (Consumption Plan, Python 3.11)
- Azure Storage Account (for blob storage with 5 containers)
- Application Insights (monitoring)
- Azure Content Understanding resource
- Azure AI Foundry Hub and Project
- Service connection for Function App → Storage Account

### 2. Configure Azure Roles

Assign necessary roles for blob storage access:

```bash
# Get your Azure subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Get your user object ID
USER_ID=$(az ad signed-in-user show --query id -o tsv)

# Assign Storage Blob Data Contributor role (allows upload/download)
az role assignment create \
  --assignee-object-id $USER_ID \
  --assignee-principal-type User \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT
```

**Note:** Role propagation takes 2-5 minutes. You must be logged in with `az login` when running Streamlit.

### 3. Set Up Python Environment

Create and activate conda environment:

```bash
# Create conda environment
conda create -n content-understanding python=3.10 -y

# Activate environment
conda activate content-understanding

# Install dependencies
cd content-understanding-agent
pip install -r requirements.txt
pip install streamlit
```

### 4. Configure Environment Variables

Create `.env` file in `content-understanding-agent` directory:

```bash
# Azure AI Foundry
PROJECT_ENDPOINT=https://<your-project>.services.ai.azure.com/api/projects/<project-name>
MODEL_DEPLOYMENT_NAME=gpt-4.1

# Azure Functions
FUNCTION_APP_URL=https://<your-function-app>.azurewebsites.net/api

# Azure Storage
STORAGE_ACCOUNT_NAME=<your-storage-account>

# Azure Content Understanding
CLASSIFIER_ID=prebuilt-layout
```

**Where to find these values:**
- `PROJECT_ENDPOINT`: Azure AI Foundry Portal → Your Project → Overview → Project Endpoint
- `MODEL_DEPLOYMENT_NAME`: Azure OpenAI Studio → Deployments → Model name
- `FUNCTION_APP_URL`: Azure Portal → Function App → Overview → URL
- `STORAGE_ACCOUNT_NAME`: Azure Portal → Storage Account → Overview → Name

**Recommended Content Understanding Analyzers:**
- `prebuilt-layout` - General document layout analysis (recommended)
- `prebuilt-read` - Text extraction only
- `prebuilt-invoice` - Invoice-specific extraction
- `prebuilt-receipt` - Receipt processing
- `prebuilt-idDocument` - ID card/passport processing

### 5. Run the Streamlit Web App

```cmd
# In Command Prompt (CMD) - not PowerShell
cd "c:\Users\<your-username>\...\content-understanding-agent"

# Activate conda environment
conda activate content-understanding

# Login to Azure (if not already logged in)
az login

# Run Streamlit
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

**Alternative:** Double-click `run_app.bat` to launch automatically.

## 📋 Azure Functions

### Function Details

| Function | Purpose | What It Does | Input | Output |
|----------|---------|--------------|-------|--------|
| **perform_ocr** | Document Analysis | Downloads document from `incoming-docs` container, sends to Azure Content Understanding API for OCR processing, extracts text, tables, and layout information, uploads OCR JSON result to `enhanced-results` container | Document filename (e.g., "invoice.pdf") | OCR JSON file in enhanced-results (e.g., "invoice_enhanced.json") |
| **parse_ocr** | Text Summarization | Downloads OCR JSON from `enhanced-results`, parses the JSON structure, extracts key information (text content, tables, confidence scores), creates human-readable text summary, uploads to `summary-reports` | OCR result blob name (e.g., "invoice_enhanced.json") | Summary text file in summary-reports (e.g., "invoice_summary.txt") |
| **create_excel** | Excel Report Generation | Downloads OCR JSON from `enhanced-results`, identifies structured data (tables, forms, key-value pairs), creates formatted Excel workbook with sheets for different data types, uploads to `excel-result` | OCR result blob name (e.g., "invoice_enhanced.json") | Excel file in excel-result (e.g., "invoice_data.xlsx") |
| **clean_up** | File Archiving | Moves original document from `incoming-docs` to `processed-docs` container after successful processing, maintains clean workflow by archiving completed documents | Document filename (e.g., "invoice.pdf") | File moved to processed-docs container |

### Validation Tools (Used by Agent)

| Tool | Purpose | What It Does |
|------|---------|--------------|
| **get_ocr_result_content** | OCR Inspection | Downloads OCR JSON from enhanced-results, analyzes content structure, returns summary of pages, tables, and data size |
| **get_parsed_summary_content** | Summary Inspection | Downloads summary text from summary-reports, analyzes content quality, returns text stats and key findings |
| **validate_ocr_and_parse** | Data Quality Check | Compares OCR JSON with parsed summary, verifies data completeness, checks for missing tables or text, validates extraction accuracy, returns detailed validation report with pass/fail status |

## 🤖 Agent Framework

The agent uses **Microsoft Agent Framework** (azure-ai-projects SDK) with:
- **Persistent Agent**: Created once, reused across sessions
- **Function Tools**: 7 registered tools (4 Azure Functions + 3 validation tools)
- **Automatic Function Calling**: Agent decides when to call functions
- **Thread-based Conversations**: Maintains context for queries

## 📦 Blob Storage Containers

- `incoming-docs` - Upload documents here for processing
- `enhanced-results` - OCR JSON outputs
- `summary-reports` - Text summaries
- `excel-result` - Generated Excel files
- `processed-docs` - Archive of processed documents

## 🚀 Usage Examples

### Process a Document
1. Upload document via web app
2. Click "Process Document"
3. Agent orchestrates: OCR → Parse → Validate → Excel → Cleanup

### Query Document Data
After processing, ask questions like:
- "What are the personal details in this document?"
- "Extract all names and addresses"
- "What is this form about?"
- "Are there any dates mentioned?"

### Python API
```python
from agent import ContentUnderstandingAgent

# Create agent (finds existing or creates new)
agent = ContentUnderstandingAgent()

# Process a document
result = agent.process_document("claims_sample.png")

if result["success"]:
    # Query the processed data
    thread_id = result["thread_id"]
    answer = agent.query("What is the plaintiff's name?", thread_id)
    print(answer)
```

## 🔧 Troubleshooting

**Upload fails with AuthorizationFailure:**
- Run `az login` in the same terminal as Streamlit
- Wait 2-5 minutes after role assignment
- Restart Streamlit to pick up new credentials

**Agent not calling functions:**
- Check `.env` has correct PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME
- Verify Azure AI Foundry project is accessible
- Check FUNCTION_APP_URL is correct

**OCR fails:**
- Supported formats: PNG, JPG, PDF
- File must be in `incoming-docs` container
- Check Azure Content Understanding resource is deployed

## 📚 Additional Documentation

- [Web App Guide](WEBAPP_README.md) - Detailed Streamlit app documentation
- [Azure Functions Deployment](../demo-azure-functions/DEPLOYMENT_SUMMARY.md) - Infrastructure details
- [Function Tools](function_tools.py) - Azure Functions wrapper code
- [Validation Tools](validation_tools.py) - Data validation functions
