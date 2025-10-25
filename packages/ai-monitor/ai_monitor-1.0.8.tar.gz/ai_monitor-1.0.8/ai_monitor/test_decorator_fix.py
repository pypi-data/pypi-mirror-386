#!/usr/bin/env python3
"""
Test script to verify the decorator token extraction fixes
"""

import logging
from unittest.mock import Mock

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_decorator_token_extraction():
    """Test that the decorator correctly extracts tokens from Azure OpenAI responses"""
    
    print("🧪 Testing Decorator Token Extraction...")
    
    # Import the extraction function
    from decorators import _extract_response_data
    
    # Test 1: OpenAI v1.x style response object
    print("\n1. Testing OpenAI v1.x response object...")
    
    # Mock the OpenAI response object structure
    mock_choice = Mock()
    mock_choice.message.content = "This is the AI response."
    
    mock_usage = Mock()
    mock_usage.prompt_tokens = 25      # What Azure provides
    mock_usage.completion_tokens = 12  # What Azure provides
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    
    # Test extraction
    response_text, input_tokens, output_tokens, cost = _extract_response_data(
        mock_response, track_tokens=True, track_cost=True
    )
    
    print(f"   Response text: {response_text}")
    print(f"   Input tokens: {input_tokens} (expected: 25)")
    print(f"   Output tokens: {output_tokens} (expected: 12)")
    
    assert input_tokens == 25, f"Expected 25 input tokens, got {input_tokens}"
    assert output_tokens == 12, f"Expected 12 output tokens, got {output_tokens}"
    print("✅ OpenAI v1.x response object test PASSED")
    
    # Test 2: Dict style response (legacy)
    print("\n2. Testing dict response...")
    
    dict_response = {
        "choices": [{
            "message": {
                "content": "This is the AI response from dict."
            }
        }],
        "usage": {
            "prompt_tokens": 35,
            "completion_tokens": 18,
            "total_tokens": 53
        }
    }
    
    response_text, input_tokens, output_tokens, cost = _extract_response_data(
        dict_response, track_tokens=True, track_cost=True
    )
    
    print(f"   Response text: {response_text}")
    print(f"   Input tokens: {input_tokens} (expected: 35)")
    print(f"   Output tokens: {output_tokens} (expected: 18)")
    
    assert input_tokens == 35, f"Expected 35 input tokens, got {input_tokens}"
    assert output_tokens == 18, f"Expected 18 output tokens, got {output_tokens}"
    print("✅ Dict response test PASSED")
    
    # Test 3: Test with missing usage (should not crash)
    print("\n3. Testing response without usage...")
    
    mock_no_usage = Mock()
    mock_no_usage.choices = [Mock()]
    mock_no_usage.choices[0].message.content = "Response without usage"
    # No usage attribute
    
    response_text, input_tokens, output_tokens, cost = _extract_response_data(
        mock_no_usage, track_tokens=True, track_cost=True
    )
    
    print(f"   Response text: {response_text}")
    print(f"   Input tokens: {input_tokens} (expected: 0)")
    print(f"   Output tokens: {output_tokens} (expected: > 0, estimated)")
    
    assert input_tokens == 0, f"Expected 0 input tokens when no usage, got {input_tokens}"
    assert output_tokens > 0, f"Expected estimated output tokens, got {output_tokens}"
    print("✅ No usage test PASSED")

if __name__ == "__main__":
    try:
        test_decorator_token_extraction()
        print("\n🎉 All decorator tests PASSED!")
        print("\nThe decorator should now correctly extract Azure OpenAI tokens.")
        print("Next step: Test with a real Azure OpenAI call to see the debug logs.")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
