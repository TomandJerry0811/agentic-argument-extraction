#!/usr/bin/env python3
"""
Test script for the Argument Cartographer backend
Tests the JSON structure generation and API response
"""

import requests
import json

def test_backend():
    # Test the Flask API
    url = "http://localhost:5000/ask"
    
    # Test payload
    test_data = {
        "question": "AI regulation in Europe"
    }
    
    try:
        print("Testing backend API...")
        response = requests.post(url, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response received successfully!")
            
            # Check if we got the structured argument map
            if 'data' in result and 'argument_map' in result:
                data_json = result['data']
                argument_map = result['argument_map']
                print(f"✅ Structured JSON data received!")
                print(f"   Title: {argument_map.get('title', 'N/A')}")
                print(f"   Elements count: {len(argument_map.get('elements', []))}")
                
                # Display the structure
                for i, element in enumerate(argument_map.get('elements', [])):
                    element_type = element.get('type', 'Unknown')
                    element_id = element.get('id', 'No ID')
                    parent_id = element.get('parentId', 'None')
                    content_preview = element.get('content', '')[:50] + '...' if len(element.get('content', '')) > 50 else element.get('content', '')
                    print(f"   Element {i+1}: {element_type} ({element_id}) -> Parent: {parent_id}")
                    print(f"     Content: {content_preview}")
                
                print("\n✅ Raw JSON String (for frontend):")
                print(data_json[:200] + "..." if len(data_json) > 200 else data_json)
            elif 'argument_map' in result:
                # Fallback for old format
                argument_map = result['argument_map']
                print(f"⚠️  Got argument_map but no data field (old format)")
                print(f"   Title: {argument_map.get('title', 'N/A')}")
                print(f"   Elements count: {len(argument_map.get('elements', []))}")
            elif 'error' in result and result['error'] == "AI returned invalid JSON format":
                print("⚠️  AI returned non-JSON response. Raw response:")
                print(result.get('raw_response', 'No raw response'))
                
            else:
                print("⚠️  Unexpected response format:")
                print(json.dumps(result, indent=2))
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_json_structure():
    """Test the expected JSON structure format"""
    print("\n" + "="*50)
    print("Expected JSON Structure:")
    print("="*50)
    
    example_structure = {
        "title": "Analysis of Recent AI Regulation in Europe",
        "elements": [
            {
                "id": "thesis-1",
                "type": "Thesis",
                "parentId": None,
                "content": "The EU's AI Act aims to establish a risk-based framework to ensure safety and fundamental rights while fostering innovation.",
                "sourceText": "The core of the legislation is a risk-based approach..."
            },
            {
                "id": "claim-1",
                "type": "Supporting Claim",
                "parentId": "thesis-1",
                "content": "The Act categorizes AI systems into four risk levels: unacceptable, high, limited, and minimal.",
                "sourceText": "AI systems are categorized as unacceptable-risk, high-risk..."
            },
            {
                "id": "evidence-1a",
                "type": "Evidence",
                "parentId": "claim-1",
                "content": "Unacceptable-risk systems like social scoring are banned outright. [Source 1]",
                "sourceText": "Article 5 of the Act bans social scoring..."
            }
        ]
    }
    
    print(json.dumps(example_structure, indent=2))

if __name__ == "__main__":
    test_json_structure()
    print("\n" + "="*50)
    print("Testing Backend API:")
    print("="*50)
    test_backend()