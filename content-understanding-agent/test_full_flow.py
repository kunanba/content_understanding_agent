"""
Test the complete flow: upload file, call function, check result
"""
import os
import requests
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

load_dotenv()

# Settings
STORAGE_ACCOUNT = os.getenv("STORAGE_ACCOUNT_NAME", "demostorageak")
FUNCTION_URL = os.getenv("FUNCTION_APP_URL", "https://func-content-understanding-2220.azurewebsites.net/api")
TEST_FILE = r"C:\Users\akunanbaeva\Downloads\claim_sample4.png"
BLOB_NAME = "test_sample_from_streamlit.png"

print("=" * 80)
print("FULL FLOW TEST")
print("=" * 80)

# Step 1: Upload file to blob
print("\n1. Uploading file to blob storage...")
try:
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=credential
    )
    blob_client = blob_service_client.get_blob_client(container="incoming-docs", blob=BLOB_NAME)
    
    with open(TEST_FILE, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    
    print(f"✅ Uploaded {BLOB_NAME}")
except Exception as e:
    print(f"❌ Upload failed: {e}")
    exit(1)

# Step 2: Call Azure Function perform_ocr
print(f"\n2. Calling perform_ocr Azure Function...")
payload = {
    "analyzer_id": "prebuilt-documentAnalyzer",
    "blob_url": f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/incoming-docs/{BLOB_NAME}",
    "storage_account_name": STORAGE_ACCOUNT
}

print(f"   Payload: {payload}")

try:
    response = requests.post(
        f"{FUNCTION_URL}/perform_ocr",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=300
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SUCCESS!")
        print(f"   Result: {result}")
    else:
        print(f"❌ FAILED!")
        print(f"   Error: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 80)
