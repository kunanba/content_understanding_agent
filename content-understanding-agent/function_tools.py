"""
Function tools that wrap Azure Functions for use by the agent.
These functions are registered as tools that the AI agent can call.
"""
import os
import requests
import json
from typing import Dict, Any
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential


def perform_ocr(blob_name: str, classifier_id: str = "prebuilt-layout") -> Dict[str, Any]:
    """
    Performs OCR on a document using Azure Content Understanding.
    
    Args:
        blob_name: Name of the blob/file in the incoming-docs container (e.g., "claims_sample3.jpg")
        classifier_id: The classifier/analyzer ID to use (default: "prebuilt-layout")
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if OCR was successful
        - result_blob_name: Name of the JSON file created with OCR results
        - container_name: Container where results are stored (enhanced-results)
        - error: Error message if failed
    """
    function_url = os.getenv("FUNCTION_APP_URL", "https://func-content-understanding-2220.azurewebsites.net/api")
    storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME", "demostorageak")
    
    # Construct the blob URL
    blob_url = f"https://{storage_account_name}.blob.core.windows.net/incoming-docs/{blob_name}"
    
    payload = {
        "analyzer_id": classifier_id,  # Azure Function expects 'analyzer_id'
        "blob_url": blob_url,
        "storage_account_name": storage_account_name
    }
    
    try:
        response = requests.post(
            f"{function_url}/perform_ocr",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minutes for OCR processing
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Get detailed error from response body
        try:
            error_detail = response.json()
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {error_detail}"
            }
        except:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:500]}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }


def parse_ocr(ocr_result_blob_name: str) -> Dict[str, Any]:
    """
    Creates a text summary from OCR results.
    
    Args:
        ocr_result_blob_name: Name of the OCR JSON blob in enhanced-results container 
                             (e.g., "claims_sample3.jpg_20251126_180248.json")
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if parsing was successful
        - summary_report_blob_name: Name of the summary text file created
        - summary_container_name: Container where summary is stored (summary-reports)
        - error: Error message if failed
    """
    function_url = os.getenv("FUNCTION_APP_URL", "https://func-content-understanding-2220.azurewebsites.net/api")
    storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME", "demostorageak")
    
    payload = {
        "ocr_result_blob_name": ocr_result_blob_name,
        "storage_account_name": storage_account_name
    }
    
    try:
        response = requests.post(
            f"{function_url}/parse_ocr",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_excel(ocr_result_blob_name: str) -> Dict[str, Any]:
    """
    Creates an Excel report from OCR results with patient information and expenses.
    
    Args:
        ocr_result_blob_name: Name of the OCR JSON blob in enhanced-results container
                             (e.g., "claims_sample3.jpg_20251126_180248.json")
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if Excel creation was successful
        - result_blob_name: Name of the Excel file created
        - container_name: Container where Excel is stored (excel-result)
        - error: Error message if failed
    """
    function_url = os.getenv("FUNCTION_APP_URL", "https://func-content-understanding-2220.azurewebsites.net/api")
    storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME", "demostorageak")
    
    payload = {
        "ocr_result_blob_name": ocr_result_blob_name,
        "storage_account_name": storage_account_name
    }
    
    try:
        response = requests.post(
            f"{function_url}/create_excel",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def clean_up(incoming_docs_blob_name: str) -> Dict[str, Any]:
    """
    Moves a processed document from incoming-docs to processed-docs container.
    
    Args:
        incoming_docs_blob_name: Name of the blob to move (e.g., "claims_sample3.jpg")
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if cleanup was successful
        - message: Success or error message
    """
    function_url = os.getenv("FUNCTION_APP_URL", "https://func-content-understanding-2220.azurewebsites.net/api")
    storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME", "demostorageak")
    
    payload = {
        "incoming_docs_blob_name": incoming_docs_blob_name,
        "storage_account_name": storage_account_name
    }
    
    try:
        response = requests.post(
            f"{function_url}/clean_up",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
