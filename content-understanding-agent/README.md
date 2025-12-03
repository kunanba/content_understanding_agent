# Content Understanding Agent

This agent orchestrates document processing workflows using Azure Functions and Microsoft Agent Framework.

## Features

- **Document Processing Workflow**: Automatically processes documents through OCR, validation, Excel creation, and cleanup
- **Data Validation**: Validates data consistency between OCR results and parsed output
- **Natural Language Queries**: Ask questions about processed document data

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   - Copy `.env.template` to `.env`
   - Fill in your Azure AI Foundry project endpoint and model deployment name

3. Ensure Azure Functions are deployed and running

## Azure Functions Used

- `perform_ocr`: Processes documents with Azure Content Understanding
- `parse_ocr`: Creates text summaries from OCR JSON
- `create_excel`: Creates Excel reports from OCR JSON
- `clean_up`: Archives processed documents

## Usage

```python
from agent import ContentUnderstandingAgent

# Create agent
agent = ContentUnderstandingAgent()

# Process a document
result = agent.process_document("claims_sample3.jpg")

# Query about the data
response = agent.query("What is the total claim amount?")
```
