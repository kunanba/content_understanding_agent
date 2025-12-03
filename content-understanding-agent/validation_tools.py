"""
Validation tools for comparing OCR results with parsed output.
These functions allow the agent to inspect actual blob contents for validation.
"""
import os
import json
from typing import Dict, Any
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential


def get_ocr_result_content(ocr_result_blob_name: str) -> Dict[str, Any]:
    """
    Downloads and returns the content of an OCR result JSON file.
    
    Args:
        ocr_result_blob_name: Name of the OCR JSON blob in enhanced-results container
                             (e.g., "claims_sample3.jpg_20251126_180248.json")
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if download was successful
        - content: The parsed JSON content from the OCR result
        - summary: A brief summary of the content (e.g., page count, table count)
        - error: Error message if failed
    """
    storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME", "demostorageak")
    container_name = "enhanced-results"
    
    try:
        # Create blob service client with DefaultAzureCredential
        account_url = f"https://{storage_account_name}.blob.core.windows.net"
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=DefaultAzureCredential()
        )
        
        # Get blob client and download
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=ocr_result_blob_name
        )
        
        blob_data = blob_client.download_blob().readall()
        content = json.loads(blob_data)
        
        # Create a summary of the content
        summary = {
            "pages": len(content.get("pages", [])),
            "has_tables": "tables" in content,
            "has_key_value_pairs": "keyValuePairs" in content,
            "content_size_bytes": len(blob_data)
        }
        
        # Add table count if present
        if "tables" in content:
            summary["table_count"] = len(content["tables"])
        
        return {
            "success": True,
            "content": content,
            "summary": summary,
            "blob_name": ocr_result_blob_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "blob_name": ocr_result_blob_name
        }


def get_parsed_summary_content(summary_blob_name: str) -> Dict[str, Any]:
    """
    Downloads and returns the content of a parsed summary text file.
    
    Args:
        summary_blob_name: Name of the summary text blob in summary-reports container
                          (e.g., "claims_sample3.jpg_20251126_180248.txt")
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if download was successful
        - content: The text content of the summary
        - line_count: Number of lines in the summary
        - char_count: Number of characters in the summary
        - error: Error message if failed
    """
    storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME", "demostorageak")
    container_name = "summary-reports"
    
    try:
        # Create blob service client with DefaultAzureCredential
        account_url = f"https://{storage_account_name}.blob.core.windows.net"
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=DefaultAzureCredential()
        )
        
        # Get blob client and download
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=summary_blob_name
        )
        
        blob_data = blob_client.download_blob().readall()
        content = blob_data.decode('utf-8')
        
        return {
            "success": True,
            "content": content,
            "line_count": len(content.split('\n')),
            "char_count": len(content),
            "blob_name": summary_blob_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "blob_name": summary_blob_name
        }


def validate_ocr_and_parse(ocr_result_blob_name: str, summary_blob_name: str) -> Dict[str, Any]:
    """
    Validates that the parsed summary contains data from the OCR results.
    
    This function downloads both files and performs validation checks:
    - Ensures both files exist and can be read
    - Checks that the summary is not empty
    - Verifies that key information from OCR appears in the summary
    - Reports any discrepancies or missing data
    
    Args:
        ocr_result_blob_name: Name of the OCR JSON blob in enhanced-results container
        summary_blob_name: Name of the summary text blob in summary-reports container
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if validation passed
        - ocr_summary: Summary of OCR content
        - parse_summary: Summary of parsed content
        - validation_checks: Dict of validation results
        - issues: List of any issues found
        - recommendations: List of recommendations if issues found
    """
    issues = []
    checks = {}
    
    try:
        # Get OCR result content
        ocr_result = get_ocr_result_content(ocr_result_blob_name)
        if not ocr_result["success"]:
            issues.append(f"Failed to read OCR result: {ocr_result.get('error')}")
            return {
                "success": False,
                "error": "Failed to read OCR result",
                "issues": issues
            }
        
        # Get parsed summary content
        parse_result = get_parsed_summary_content(summary_blob_name)
        if not parse_result["success"]:
            issues.append(f"Failed to read parsed summary: {parse_result.get('error')}")
            return {
                "success": False,
                "error": "Failed to read parsed summary",
                "issues": issues
            }
        
        # Validation check 1: Summary is not empty
        checks["summary_not_empty"] = len(parse_result["content"].strip()) > 0
        if not checks["summary_not_empty"]:
            issues.append("Parsed summary is empty")
        
        # Validation check 2: Summary has reasonable length
        min_expected_length = 50  # At least 50 characters
        checks["summary_sufficient_length"] = parse_result["char_count"] >= min_expected_length
        if not checks["summary_sufficient_length"]:
            issues.append(f"Summary is too short ({parse_result['char_count']} chars, expected at least {min_expected_length})")
        
        # Validation check 3: Extract some text from OCR and check if it's in summary
        ocr_content = ocr_result["content"]
        if "pages" in ocr_content and len(ocr_content["pages"]) > 0:
            # Try to extract some content from the first page
            first_page = ocr_content["pages"][0]
            if "lines" in first_page and len(first_page["lines"]) > 0:
                # Get a sample of text from first few lines
                sample_texts = []
                for line in first_page["lines"][:3]:  # First 3 lines
                    if "content" in line:
                        sample_texts.append(line["content"])
                
                # Check if any of the sample text appears in summary
                summary_lower = parse_result["content"].lower()
                found_matches = 0
                for text in sample_texts:
                    if text.lower() in summary_lower:
                        found_matches += 1
                
                checks["ocr_text_in_summary"] = found_matches > 0
                if not checks["ocr_text_in_summary"]:
                    issues.append("Could not find any OCR text content in the parsed summary")
        
        # Validation check 4: If OCR has tables, summary should mention data
        if ocr_result["summary"].get("has_tables"):
            checks["tables_processed"] = "table" in parse_result["content"].lower() or \
                                        "data" in parse_result["content"].lower() or \
                                        len(parse_result["content"]) > 200
            if not checks["tables_processed"]:
                issues.append("OCR contains tables but they may not be properly represented in summary")
        
        # Overall validation result
        all_checks_passed = all(checks.values())
        
        result = {
            "success": all_checks_passed,
            "ocr_summary": ocr_result["summary"],
            "parse_summary": {
                "line_count": parse_result["line_count"],
                "char_count": parse_result["char_count"]
            },
            "validation_checks": checks,
            "issues": issues if issues else ["No issues found"],
            "overall_status": "PASSED" if all_checks_passed else "FAILED"
        }
        
        # Add recommendations if there are issues
        if issues and not all_checks_passed:
            result["recommendations"] = [
                "Review the parse_ocr function to ensure it's properly extracting data",
                "Check if the OCR result format matches what parse_ocr expects",
                "Verify the summary generation logic is working correctly"
            ]
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "issues": issues + [f"Validation error: {str(e)}"]
        }
