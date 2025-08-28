#!/usr/bin/env python3
"""
Simple Data Ingestion Example

This script demonstrates how to ingest call data into Voice Summary
using the REST API. Perfect for custom integrations and testing.
"""

import requests
import json
from datetime import datetime, timezone
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{API_BASE_URL}/api/calls/"

def create_sample_call_data() -> Dict[str, Any]:
    """Create sample call data for testing."""
    
    # Base timestamp for the call
    call_time = datetime.now(timezone.utc)
    
    # Sample conversation turns
    turns = [
        {
            "role": "AGENT",
            "content": "Hello! Thank you for calling our support line. How can I assist you today?",
            "timestamp": call_time.isoformat()
        },
        {
            "role": "USER",
            "content": "Hi, I'm having trouble with my recent order. The tracking number isn't working.",
            "timestamp": (call_time.replace(second=call_time.second + 2)).isoformat()
        },
        {
            "role": "AGENT", 
            "content": "I understand that can be frustrating. Let me help you track down your order. Can you provide me with your order number?",
            "timestamp": (call_time.replace(second=call_time.second + 5)).isoformat()
        },
        {
            "role": "USER",
            "content": "Yes, it's ORD-2025-001. I placed it last week.",
            "timestamp": (call_time.replace(second=call_time.second + 8)).isoformat()
        },
        {
            "role": "AGENT",
            "content": "Perfect, I can see your order ORD-2025-001. It was shipped yesterday and should arrive by Friday. Let me get you the updated tracking information.",
            "timestamp": (call_time.replace(second=call_time.second + 12)).isoformat()
        }
    ]
    
    return {
        "call_id": f"sample_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "transcript": {
            "turns": turns,
            "metadata": {
                "total_turns": len(turns),
                "call_type": "customer_support",
                "language": "en-US"
            }
        },
        "timestamp": call_time.isoformat(),
        "metadata": {
            "call_duration_seconds": 15,
            "participants": ["support_agent", "customer"],
            "call_quality": "good",
            "notes": "Sample call for testing purposes"
        }
    }

def create_call_with_audio_url() -> Dict[str, Any]:
    """Create call data with an S3 audio file URL."""
    
    call_data = create_sample_call_data()
    
    # Add S3 audio file URL (replace with your actual S3 URL)
    call_data["audio_file_url"] = "https://your-s3-bucket.s3.amazonaws.com/audio/sample_call.mp3"
    
    return call_data

def ingest_call(call_data: Dict[str, Any]) -> bool:
    """Ingest a call into Voice Summary via API."""
    
    try:
        print(f"📤 Ingesting call: {call_data['call_id']}")
        
        response = requests.post(
            API_ENDPOINT,
            json=call_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully ingested call: {call_data['call_id']}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Failed to ingest call: {call_data['call_id']}")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while ingesting call: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_health() -> bool:
    """Test if the Voice Summary API is running."""
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy and running")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API. Is the server running?")
        return False

def list_existing_calls() -> None:
    """List all existing calls in the system."""
    
    try:
        response = requests.get(API_ENDPOINT)
        if response.status_code == 200:
            calls = response.json()
            print(f"\n📋 Found {len(calls)} existing calls:")
            for call in calls[:5]:  # Show first 5
                print(f"   - {call['call_id']} ({call['timestamp']})")
            if len(calls) > 5:
                print(f"   ... and {len(calls) - 5} more calls")
        else:
            print(f"❌ Failed to fetch calls: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching calls: {e}")

def main():
    """Main function to demonstrate data ingestion."""
    
    print("🎤 Voice Summary - Data Ingestion Example")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("\n💡 Make sure to:")
        print("   1. Start the backend server: ./start_backend.sh")
        print("   2. Check your .env configuration")
        print("   3. Ensure PostgreSQL is running")
        return
    
    # List existing calls
    list_existing_calls()
    
    print("\n" + "=" * 50)
    print("📥 Starting Data Ingestion")
    print("=" * 50)
    
    # Ingest sample call without audio
    sample_call = create_sample_call_data()
    success1 = ingest_call(sample_call)
    
    # Ingest sample call with audio URL
    audio_call = create_call_with_audio_url()
    success2 = ingest_call(audio_call)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Ingestion Summary")
    print("=" * 50)
    
    if success1 and success2:
        print("🎉 All calls ingested successfully!")
        print("\n💡 Next steps:")
        print("   1. Open http://localhost:3000 to view your calls")
        print("   2. Check the API docs at http://localhost:8000/docs")
        print("   3. Try ingesting your own call data")
    else:
        print("⚠️  Some calls failed to ingest. Check the errors above.")
    
    print("\n🔍 View your calls:")
    print(f"   - Frontend: http://localhost:3000")
    print(f"   - API: {API_ENDPOINT}")

if __name__ == "__main__":
    main()
