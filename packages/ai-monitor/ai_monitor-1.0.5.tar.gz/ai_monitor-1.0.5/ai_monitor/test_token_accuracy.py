#!/usr/bin/env python3
"""
Test script to verify token counting accuracy against Azure OpenAI
"""

import json
import logging
from unittest.mock import Mock
from http_interceptor import extract_openai_data, validate_azure_tokens

# Set up logging to see debug output
logging.basicConfig(level=logging.INFO)

def test_azure_token_extraction():
    """Test that we correctly extract and preserve Azure-provided tokens"""
    
    print("🧪 Testing Azure Token Extraction...")
    
    # Simulate Azure OpenAI response with actual token counts
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "This is a test response from Azure OpenAI."
            }
        }],
        "usage": {
            "prompt_tokens": 25,      # This is what Azure reports
            "completion_tokens": 12,  # This is what Azure reports  
            "total_tokens": 37        # This is what Azure reports
        }
    }
    
    # Simulate request data
    request_data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Hello, this is a test message for token counting."}
        ]
    }
    
    # Test Azure OpenAI URL
    url = "https://test.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
    
    # Extract the data
    result = extract_openai_data(url, request_data, {}, mock_response)
    
    print(f"\n📊 Results:")
    print(f"   Model: {result['model']}")
    print(f"   Input tokens: {result['input_tokens']} (Azure provided: 25)")
    print(f"   Output tokens: {result['output_tokens']} (Azure provided: 12)")
    print(f"   Total tokens: {result['total_tokens']} (Azure provided: 37)")
    
    # Verify we're using Azure's exact values
    assert result['input_tokens'] == 25, f"Expected 25 input tokens, got {result['input_tokens']}"
    assert result['output_tokens'] == 12, f"Expected 12 output tokens, got {result['output_tokens']}" 
    assert result['total_tokens'] == 37, f"Expected 37 total tokens, got {result['total_tokens']}"
    
    print("✅ Test PASSED: Azure tokens preserved exactly!")
    
def test_missing_azure_tokens():
    """Test fallback when Azure doesn't provide tokens"""
    
    print("\n🧪 Testing Fallback Token Calculation...")
    
    # Simulate response without usage data (some endpoints might not provide it)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "This is a response without usage data."
            }
        }]
        # No "usage" field
    }
    
    request_data = {
        "model": "gpt-4o", 
        "messages": [
            {"role": "user", "content": "This is a longer test message to see how well our token estimation works when Azure doesn't provide the actual token counts."}
        ]
    }
    
    url = "https://test.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
    
    result = extract_openai_data(url, request_data, {}, mock_response)
    
    print(f"\n📊 Fallback Results:")
    print(f"   Model: {result['model']}")
    print(f"   Input tokens: {result['input_tokens']} (estimated)")
    print(f"   Output tokens: {result['output_tokens']} (estimated)")
    print(f"   Total tokens: {result['total_tokens']} (estimated)")
    
    # Should have some reasonable token counts
    assert result['input_tokens'] > 0, "Should estimate input tokens when Azure doesn't provide them"
    assert result['total_tokens'] > 0, "Should have total tokens"
    
    print("✅ Test PASSED: Fallback estimation working!")

def test_token_validation():
    """Test the token validation function"""
    
    print("\n🧪 Testing Token Validation...")
    
    # Test valid tokens
    is_valid, total = validate_azure_tokens(25, 12, 37, "Test")
    assert is_valid and total == 37, "Valid tokens should pass validation"
    
    # Test mismatched total (should correct it)
    is_valid, total = validate_azure_tokens(25, 12, 40, "Test")  
    assert is_valid and total == 37, "Should correct mismatched total"
    
    # Test zero input tokens (should fail validation)
    is_valid, total = validate_azure_tokens(0, 12, 12, "Test")
    assert not is_valid, "Zero input tokens should fail validation"
    
    print("✅ Test PASSED: Token validation working!")

if __name__ == "__main__":
    try:
        test_azure_token_extraction()
        test_missing_azure_tokens() 
        test_token_validation()
        print("\n🎉 All tests PASSED! Token handling should now match Azure exactly.")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
