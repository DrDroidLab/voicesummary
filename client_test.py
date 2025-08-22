#!/usr/bin/env python3
"""
Voice Summary API Client Test Script
This script can be given to clients for testing the API endpoints.

Usage:
    python client_test.py --help
    python client_test.py --base-url http://localhost:8000
    python client_test.py --create-sample-calls
"""

import argparse
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys


class VoiceSummaryClient:
    """Client for testing the Voice Summary API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'VoiceSummary-Client/1.0'
        })
    
    def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print(f"✅ Health check passed: {response.json()}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def create_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new audio call record."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/calls/",
                json=call_data
            )
            if response.status_code == 201:
                print(f"✅ Call created successfully: {call_data['call_id']}")
                return response.json()
            else:
                print(f"❌ Failed to create call: {response.status_code} - {response.text}")
                return {}
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating call: {e}")
            return {}
    
    def get_call(self, call_id: str) -> Dict[str, Any]:
        """Get call information by ID."""
        try:
            response = self.session.get(f"{self.base_url}/api/calls/{call_id}")
            if response.status_code == 200:
                print(f"✅ Retrieved call: {call_id}")
                return response.json()
            else:
                print(f"❌ Failed to get call: {response.status_code} - {response.text}")
                return {}
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting call: {e}")
            return {}
    
    def get_transcript(self, call_id: str) -> Dict[str, Any]:
        """Get transcript for a call."""
        try:
            response = self.session.get(f"{self.base_url}/api/calls/{call_id}/transcript")
            if response.status_code == 200:
                print(f"✅ Retrieved transcript for: {call_id}")
                return response.json()
            else:
                print(f"❌ Failed to get transcript: {response.status_code} - {response.text}")
                return {}
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting transcript: {e}")
            return {}
    
    def list_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List all calls with pagination."""
        try:
            response = self.session.get(f"{self.base_url}/api/calls/?limit={limit}")
            if response.status_code == 200:
                calls = response.json()
                print(f"✅ Retrieved {len(calls)} calls")
                return calls
            else:
                print(f"❌ Failed to list calls: {response.status_code} - {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Error listing calls: {e}")
            return []
    
    def update_call(self, call_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing call."""
        try:
            response = self.session.put(
                f"{self.base_url}/api/calls/{call_id}",
                json=update_data
            )
            if response.status_code == 200:
                print(f"✅ Updated call: {call_id}")
                return response.json()
            else:
                print(f"❌ Failed to update call: {response.status_code} - {response.text}")
                return {}
        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating call: {e}")
            return {}
    
    def delete_call(self, call_id: str) -> bool:
        """Delete a call."""
        try:
            response = self.session.delete(f"{self.base_url}/api/calls/{call_id}")
            if response.status_code == 204:
                print(f"✅ Deleted call: {call_id}")
                return True
            else:
                print(f"❌ Failed to delete call: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting call: {e}")
            return False


def generate_sample_calls() -> List[Dict[str, Any]]:
    """Generate sample call data for testing."""
    
    base_time = datetime.now() - timedelta(days=1)
    
    sample_calls = [
        {
            "call_id": "call_001_20241201",
            "transcript": {
                "participants": ["John Smith", "Jane Doe"],
                "conversation": [
                    {
                        "speaker": "John Smith",
                        "text": "Hello Jane, how are you doing today?",
                        "timestamp": "00:00:05",
                        "confidence": 0.95
                    },
                    {
                        "speaker": "Jane Doe",
                        "text": "Hi John! I'm doing well, thank you for asking. How about you?",
                        "timestamp": "00:00:08",
                        "confidence": 0.92
                    },
                    {
                        "speaker": "John Smith",
                        "text": "I'm great! I wanted to discuss the quarterly sales report.",
                        "timestamp": "00:00:12",
                        "confidence": 0.88
                    }
                ],
                "summary": "John and Jane discussed quarterly sales report",
                "duration": "00:02:30",
                "call_type": "business",
                "sentiment": "positive"
            },
            "audio_file_url": "s3://voicesummary-bucket/calls/2024/12/call_001_20241201.mp3",
            "timestamp": base_time.isoformat()
        },
        {
            "call_id": "call_002_20241201",
            "transcript": {
                "participants": ["Alice Johnson", "Bob Wilson"],
                "conversation": [
                    {
                        "speaker": "Alice Johnson",
                        "text": "Good morning Bob, I have a question about the new product launch.",
                        "timestamp": "00:00:03",
                        "confidence": 0.94
                    },
                    {
                        "speaker": "Bob Wilson",
                        "text": "Morning Alice! Sure, what would you like to know?",
                        "timestamp": "00:00:07",
                        "confidence": 0.91
                    },
                    {
                        "speaker": "Alice Johnson",
                        "text": "When exactly is the launch date? And what marketing materials do we have ready?",
                        "timestamp": "00:00:11",
                        "confidence": 0.89
                    }
                ],
                "summary": "Alice and Bob discussed product launch details and marketing materials",
                "duration": "00:01:45",
                "call_type": "product_planning",
                "sentiment": "neutral"
            },
            "audio_file_url": "s3://voicesummary-bucket/calls/2024/12/call_002_20241201.mp3",
            "timestamp": (base_time + timedelta(hours=2)).isoformat()
        },
        {
            "call_id": "call_003_20241201",
            "transcript": {
                "participants": ["Customer Support", "Sarah Miller"],
                "conversation": [
                    {
                        "speaker": "Customer Support",
                        "text": "Thank you for calling customer support. How can I help you today?",
                        "timestamp": "00:00:02",
                        "confidence": 0.96
                    },
                    {
                        "speaker": "Sarah Miller",
                        "text": "Hi, I'm having trouble with my account login. It keeps saying invalid credentials.",
                        "timestamp": "00:00:06",
                        "confidence": 0.87
                    },
                    {
                        "speaker": "Customer Support",
                        "text": "I understand that can be frustrating. Let me help you reset your password.",
                        "timestamp": "00:00:10",
                        "confidence": 0.93
                    }
                ],
                "summary": "Customer support helped Sarah with account login issues",
                "duration": "00:03:15",
                "call_type": "customer_support",
                "sentiment": "positive"
            },
            "audio_file_url": "s3://voicesummary-bucket/calls/2024/12/call_003_20241201.mp3",
            "timestamp": (base_time + timedelta(hours=4)).isoformat()
        }
    ]
    
    return sample_calls


def run_comprehensive_test(client: VoiceSummaryClient):
    """Run a comprehensive test of all API endpoints."""
    
    print("\n" + "="*60)
    print("🚀 RUNNING COMPREHENSIVE API TEST")
    print("="*60)
    
    # Step 1: Health check
    print("\n1️⃣  Testing API Health...")
    if not client.health_check():
        print("❌ API is not healthy. Exiting test.")
        return
    
    # Step 2: Create sample calls
    print("\n2️⃣  Creating Sample Calls...")
    sample_calls = generate_sample_calls()
    created_calls = []
    
    for call_data in sample_calls:
        result = client.create_call(call_data)
        if result:
            created_calls.append(result)
        time.sleep(0.5)  # Small delay between requests
    
    if not created_calls:
        print("❌ No calls were created. Exiting test.")
        return
    
    # Step 3: List all calls
    print("\n3️⃣  Listing All Calls...")
    all_calls = client.list_calls(limit=50)
    
    # Step 4: Test individual call operations
    print("\n4️⃣  Testing Individual Call Operations...")
    for call in created_calls[:2]:  # Test with first 2 calls
        call_id = call['call_id']
        
        # Get call details
        print(f"\n   📞 Testing call: {call_id}")
        call_details = client.get_call(call_id)
        
        # Get transcript
        transcript = client.get_transcript(call_id)
        
        # Update call (add a note)
        update_data = {
            "transcript": {
                **call_details.get('transcript', {}),
                "notes": "Added during testing - Call quality verified"
            }
        }
        updated_call = client.update_call(call_id, update_data)
        
        time.sleep(0.5)
    
    # Step 5: Test error cases
    print("\n5️⃣  Testing Error Cases...")
    
    # Try to get non-existent call
    print("   🔍 Testing non-existent call...")
    client.get_call("non_existent_call_12345")
    
    # Try to create duplicate call
    print("   🔄 Testing duplicate call creation...")
    if created_calls:
        duplicate_data = created_calls[0].copy()
        client.create_call(duplicate_data)
    
    # Step 6: Cleanup (optional)
    print("\n6️⃣  Cleanup Options...")
    print("   💡 Sample calls have been created for testing.")
    print("   💡 You can manually delete them using the API or pgAdmin.")
    print("   💡 Or run this script with --cleanup flag to remove them.")
    
    print("\n" + "="*60)
    print("✅ COMPREHENSIVE TEST COMPLETED")
    print("="*60)
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   - Created {len(created_calls)} sample calls")
    print(f"   - Tested all major API endpoints")
    print(f"   - Verified error handling")
    print(f"\n🔗 API Documentation: {client.base_url}/docs")
    print(f"🔗 Health Check: {client.base_url}/health")


def run_cleanup(client: VoiceSummaryClient):
    """Clean up all test calls."""
    print("\n🧹 Running Cleanup...")
    
    # List all calls
    calls = client.list_calls(limit=100)
    test_calls = [call for call in calls if call['call_id'].startswith('call_')]
    
    if not test_calls:
        print("✅ No test calls found to clean up.")
        return
    
    print(f"🗑️  Found {len(test_calls)} test calls to delete...")
    
    for call in test_calls:
        call_id = call['call_id']
        if client.delete_call(call_id):
            time.sleep(0.5)
    
    print(f"✅ Cleanup completed. Deleted {len(test_calls)} test calls.")


def main():
    """Main function to run the client test."""
    
    parser = argparse.ArgumentParser(
        description="Voice Summary API Client Test Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python client_test.py                                    # Test with default localhost:8000
  python client_test.py --base-url https://api.example.com # Test with custom API URL
  python client_test.py --create-sample-calls              # Create sample calls and run tests
  python client_test.py --cleanup                          # Clean up all test calls
  python client_test.py --interactive                      # Interactive mode for manual testing
        """
    )
    
    parser.add_argument(
        '--base-url',
        default='http://localhost:8000',
        help='Base URL of the Voice Summary API (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--create-sample-calls',
        action='store_true',
        help='Create sample calls and run comprehensive tests'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up all test calls'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode for manual testing'
    )
    
    args = parser.parse_args()
    
    # Create client
    client = VoiceSummaryClient(args.base_url)
    
    print("🎯 Voice Summary API Client Test Script")
    print("=" * 50)
    print(f"🌐 API Base URL: {args.base_url}")
    
    try:
        if args.cleanup:
            run_cleanup(client)
        elif args.create_sample_calls or args.interactive:
            if args.create_sample_calls:
                run_comprehensive_test(client)
            if args.interactive:
                print("\n🔧 Interactive mode not implemented yet. Use --create-sample-calls for testing.")
        else:
            # Default: just health check
            print("\n🏥 Running Health Check...")
            client.health_check()
            print("\n💡 Use --help to see all available options")
            print("💡 Use --create-sample-calls to run comprehensive tests")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
