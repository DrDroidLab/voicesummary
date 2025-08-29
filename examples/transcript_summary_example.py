#!/usr/bin/env python3
"""
Example script demonstrating transcript summarization functionality.
This script shows how to:
1. Create a call with automatic transcript summarization
2. View the generated summary
3. Regenerate the summary using the API endpoint
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
CALL_ID = f"summary_example_{int(time.time())}"

# Sample transcript data
SAMPLE_TRANSCRIPT = {
    "turns": [
        {
            "role": "agent",
            "content": "Hello! Thank you for calling our customer support line. My name is Sarah, and I'm here to help you today. How may I assist you?",
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "role": "customer",
            "content": "Hi Sarah, I'm having trouble with my account login. I keep getting an error message when I try to sign in.",
            "timestamp": "2024-01-15T10:00:15Z"
        },
        {
            "role": "agent",
            "content": "I understand that can be frustrating. Let me help you resolve this login issue. Can you tell me what specific error message you're seeing?",
            "timestamp": "2024-01-15T10:00:30Z"
        },
        {
            "role": "customer",
            "content": "It says 'Invalid credentials' but I know my password is correct.",
            "timestamp": "2024-01-15T10:00:45Z"
        },
        {
            "role": "agent",
            "content": "Thank you for that information. Let me check your account status. Can you confirm your email address so I can look up your account?",
            "timestamp": "2024-01-15T10:01:00Z"
        },
        {
            "role": "customer",
            "content": "Sure, it's customer@example.com",
            "timestamp": "2024-01-15T10:01:15Z"
        },
        {
            "role": "agent",
            "content": "Perfect, I can see your account. It looks like your account was temporarily locked due to multiple failed login attempts. I can unlock it for you right now. Would you like me to do that?",
            "timestamp": "2024-01-15T10:01:45Z"
        },
        {
            "role": "customer",
            "content": "Yes, please! That would be great.",
            "timestamp": "2024-01-15T10:02:00Z"
        },
        {
            "role": "agent",
            "content": "Excellent! I've unlocked your account. You should now be able to log in successfully. I also recommend changing your password to something unique if you haven't done so recently. Is there anything else I can help you with today?",
            "timestamp": "2024-01-15T10:02:15Z"
        },
        {
            "role": "customer",
            "content": "No, that's all I needed. Thank you so much for your help, Sarah!",
            "timestamp": "2024-01-15T10:02:30Z"
        },
        {
            "role": "agent",
            "content": "You're very welcome! I'm glad I could help resolve your login issue. Have a wonderful day, and don't hesitate to call back if you need anything else. Goodbye!",
            "timestamp": "2024-01-15T10:02:45Z"
        }
    ],
    "participants": ["agent", "customer"],
    "duration": 165,
    "call_type": "customer_support"
}

def create_call_with_summary():
    """Create a call with automatic transcript summarization."""
    
    print(f"🚀 Creating call with transcript summarization...")
    print(f"Call ID: {CALL_ID}")
    print()
    
    # Create call data
    call_data = {
        "call_id": CALL_ID,
        "transcript": SAMPLE_TRANSCRIPT,
        "audio_file_url": "https://example.com/sample-audio.mp3",  # Placeholder URL
        "call_context": "Customer experiencing login issues, needs account unlocked",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Create the call
        response = requests.post(
            f"{API_BASE_URL}/api/calls/",
            json=call_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            call_result = response.json()
            print("✅ Call created successfully!")
            print(f"   Call ID: {call_result['call_id']}")
            print(f"   Timestamp: {call_result['timestamp']}")
            
            # Check if transcript summary was generated
            if call_result.get('processed_data', {}).get('transcript_summary'):
                print("✅ Transcript summary generated automatically!")
                return call_result
            else:
                print("⚠️  Call created but transcript summary not generated")
                return call_result
        else:
            print(f"❌ Failed to create call: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def regenerate_summary():
    """Regenerate transcript summary using the API endpoint."""
    
    print(f"\n🔄 Regenerating transcript summary...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/calls/{CALL_ID}/summarize-transcript",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Transcript summary regenerated successfully!")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            return result
        else:
            print(f"❌ Summary regeneration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def get_call_details():
    """Retrieve and display call details including summary."""
    
    print(f"\n📋 Retrieving call details...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/calls/{CALL_ID}")
        
        if response.status_code == 200:
            call_details = response.json()
            print("✅ Call details retrieved!")
            print(f"   Call ID: {call_details['call_id']}")
            print(f"   Timestamp: {call_details['timestamp']}")
            
            # Check for processed data
            if call_details.get('processed_data'):
                print("   ✅ Has processed data")
                
                # Check for transcript summary
                if call_details['processed_data'].get('transcript_summary'):
                    summary = call_details['processed_data']['transcript_summary']
                    print("   ✅ Has transcript summary")
                    
                    # Display summary key information
                    if 'executive_summary' in summary:
                        print(f"      Executive Summary: {summary['executive_summary'][:100]}...")
                    
                    if 'call_outcome' in summary:
                        print(f"      Call Outcome: {summary['call_outcome']}")
                    
                    if 'call_quality' in summary and summary['call_quality'].get('overall_rating'):
                        print(f"      Overall Rating: {summary['call_quality']['overall_rating']}")
                    
                    if 'key_topics' in summary and summary['key_topics']:
                        print(f"      Key Topics: {', '.join(summary['key_topics'][:3])}")
                    
                    if 'metadata' in summary:
                        print(f"      Generated using: {summary['metadata'].get('model_used', 'Unknown')}")
                else:
                    print("   ❌ No transcript summary found")
                
                # Check for other processed data
                if call_details['processed_data'].get('agent_analysis'):
                    print("   ✅ Has agent analysis")
                if call_details['processed_data'].get('summary'):
                    print("   ✅ Has call health summary")
            else:
                print("   ❌ No processed data found")
            
            return call_details
        else:
            print(f"❌ Failed to retrieve call: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    """Main function to demonstrate the transcript summarization functionality."""
    
    print("=" * 60)
    print("📋 TRANSCRIPT SUMMARIZATION DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Step 1: Create a call with automatic summarization
    call_result = create_call_with_summary()
    if not call_result:
        print("❌ Cannot continue without creating a call")
        return
    
    # Wait a moment for processing
    print("\n⏳ Waiting for processing to complete...")
    time.sleep(3)
    
    # Step 2: Get call details to see the summary
    call_details = get_call_details()
    if not call_details:
        print("❌ Cannot retrieve call details")
        return
    
    # Step 3: Regenerate summary using the API endpoint
    regeneration_result = regenerate_summary()
    if not regeneration_result:
        print("❌ Cannot regenerate summary")
        return
    
    # Step 4: Get updated call details
    print("\n⏳ Waiting for summary regeneration to complete...")
    time.sleep(2)
    
    updated_call = get_call_details()
    
    print("\n" + "=" * 60)
    print("🎉 DEMONSTRATION COMPLETED!")
    print("=" * 60)
    print()
    print("What was demonstrated:")
    print("✅ Created a call with automatic transcript summarization")
    print("✅ Retrieved call details including AI-generated summary")
    print("✅ Regenerated transcript summary using the API endpoint")
    print()
    print("Next steps:")
    print("1. View the call in the web interface")
    print("2. Explore the transcript summary at the top of the page")
    print("3. Use the 'Regenerate Summary' button if needed")
    print("4. Check the detailed summary with expandable sections")
    print()
    print(f"Call ID for reference: {CALL_ID}")
    print()
    print("The transcript summary will appear at the very top of the call details page,")
    print("above the agent analysis and other call information.")

if __name__ == "__main__":
    main()
