#!/usr/bin/env python3
"""
Example script demonstrating how to use the new asynchronous API endpoints for call processing.

This script shows how to:
1. Create a call record via API (immediate response)
2. Start background processing during creation
3. Check processing status
4. Process an existing call later
5. Use the full processing pipeline (same as Bolna integration)

Usage:
    python api_call_processing_example.py

Environment Variables Required:
    - API_BASE_URL: Base URL of your Voice Summary API (default: http://localhost:8000)
    - DATABASE_URL: PostgreSQL connection string (for direct database access if needed)
"""

import os
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
API_ENDPOINTS = {
    'create_call': f"{API_BASE_URL}/api/calls/",
    'create_and_process': f"{API_BASE_URL}/api/calls/create-and-process",
    'process_full': f"{API_BASE_URL}/api/calls/{{call_id}}/process-full",
    'get_call': f"{API_BASE_URL}/api/calls/{{call_id}}",
    'get_status': f"{API_BASE_URL}/api/calls/{{call_id}}/status",
    'list_calls': f"{API_BASE_URL}/api/calls/",
    'get_transcript': f"{API_BASE_URL}/api/calls/{{call_id}}/transcript",
    'download_audio': f"{API_BASE_URL}/api/calls/{{call_id}}/audio"
}


class VoiceSummaryAPIClient:
    """Client for interacting with the Voice Summary API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_call(self, call_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new call record without processing."""
        try:
            response = self.session.post(API_ENDPOINTS['create_call'], json=call_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create call: {e}")
            return None
    
    def create_and_process_call(self, call_data: Dict[str, Any], process_immediately: bool = True) -> Optional[Dict[str, Any]]:
        """Create a new call record and optionally start background processing."""
        try:
            # Add the processing flag
            call_data['process_immediately'] = process_immediately
            
            response = self.session.post(API_ENDPOINTS['create_and_process'], json=call_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create and process call: {e}")
            return None
    
    def get_call_status(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get the processing status of a call."""
        try:
            response = self.session.get(API_ENDPOINTS['get_status'].format(call_id=call_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get status for call {call_id}: {e}")
            return None
    
    def process_existing_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Process an existing call using the full processing pipeline."""
        try:
            response = self.session.post(API_ENDPOINTS['process_full'].format(call_id=call_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to process call {call_id}: {e}")
            return None
    
    def get_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call information by ID."""
        try:
            response = self.session.get(API_ENDPOINTS['get_call'].format(call_id=call_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get call {call_id}: {e}")
            return None
    
    def list_calls(self, skip: int = 0, limit: int = 10) -> Optional[list]:
        """List calls with pagination."""
        try:
            params = {'skip': skip, 'limit': limit}
            response = self.session.get(API_ENDPOINTS['list_calls'], params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list calls: {e}")
            return None
    
    def get_transcript(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript for a specific call."""
        try:
            response = self.session.get(API_ENDPOINTS['get_transcript'].format(call_id=call_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get transcript for call {call_id}: {e}")
            return None
    
    def wait_for_processing(self, call_id: str, max_wait_time: int = 300, check_interval: int = 5) -> Optional[Dict[str, Any]]:
        """
        Wait for a call to finish processing.
        
        Args:
            call_id: The call ID to monitor
            max_wait_time: Maximum time to wait in seconds (default: 5 minutes)
            check_interval: How often to check status in seconds (default: 5 seconds)
            
        Returns:
            Final status or None if timeout
        """
        start_time = time.time()
        logger.info(f"Waiting for call {call_id} to finish processing...")
        
        while time.time() - start_time < max_wait_time:
            status = self.get_call_status(call_id)
            if not status:
                logger.warning(f"Could not get status for call {call_id}")
                time.sleep(check_interval)
                continue
            
            logger.info(f"Call {call_id} status: {status['status']} - {status['message']}")
            
            if status['status'] == 'completed':
                logger.info(f"Call {call_id} processing completed!")
                return status
            elif status['status'] == 'partially_processed':
                logger.info(f"Call {call_id} partially processed, continuing to wait...")
            elif status['status'] == 'pending':
                logger.info(f"Call {call_id} still pending, continuing to wait...")
            
            time.sleep(check_interval)
        
        logger.warning(f"Timeout waiting for call {call_id} to finish processing")
        return None


def create_sample_transcript() -> Dict[str, Any]:
    """Create a sample transcript in the expected format."""
    return {
        "turns": [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "role": "AGENT",
                "content": "Hello, thank you for calling our customer service. How can I help you today?"
            },
            {
                "timestamp": "2024-01-01T10:00:05Z",
                "role": "USER",
                "content": "Hi, I have a question about my recent order."
            },
            {
                "timestamp": "2024-01-01T10:00:10Z",
                "role": "AGENT",
                "content": "I'd be happy to help with your order. Could you please provide your order number?"
            },
            {
                "timestamp": "2024-01-01T10:00:15Z",
                "role": "USER",
                "content": "Yes, it's ORD-12345."
            },
            {
                "timestamp": "2024-01-01T10:00:20Z",
                "role": "AGENT",
                "content": "Thank you. I can see your order ORD-12345. It was shipped yesterday and should arrive within 2-3 business days."
            }
        ],
        "format": "conversation",
        "metadata": {
            "source": "api_example",
            "total_turns": 5,
            "duration_seconds": 20
        }
    }


def create_sample_call_data(call_id: str, audio_url: str) -> Dict[str, Any]:
    """Create sample call data for testing."""
    return {
        "call_id": call_id,
        "transcript": create_sample_transcript(),
        "audio_file_url": audio_url,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """Main function demonstrating the API usage."""
    logger.info("Starting Voice Summary API example...")
    
    # Initialize API client
    client = VoiceSummaryAPIClient()
    
    # Test 1: Create a call without processing
    logger.info("\n=== Test 1: Create call without processing ===")
    sample_call_data = create_sample_call_data(
        call_id="test_call_001",
        audio_url="https://example.com/audio/sample_call_001.mp3"
    )
    
    created_call = client.create_call(sample_call_data)
    if created_call:
        logger.info(f"Successfully created call: {created_call['call_id']}")
        logger.info(f"Call status: created_at={created_call['created_at']}")
    else:
        logger.error("Failed to create call")
        return
    
    # Test 2: Create and start background processing
    logger.info("\n=== Test 2: Create and start background processing ===")
    sample_call_data_2 = create_sample_call_data(
        call_id="test_call_002",
        audio_url="https://example.com/audio/sample_call_002.mp3"
    )
    
    # This will return immediately and start background processing
    processed_call = client.create_and_process_call(sample_call_data_2, process_immediately=True)
    if processed_call:
        logger.info(f"Successfully created call: {processed_call['call_id']}")
        logger.info(f"Processing status: {processed_call['status']}")
        logger.info(f"Message: {processed_call['message']}")
        
        # Check the initial status
        initial_status = client.get_call_status(processed_call['call_id'])
        if initial_status:
            logger.info(f"Initial status: {initial_status['status']} - {initial_status['message']}")
        
        # Note: In a real scenario, you would wait for processing to complete
        # For demo purposes, we'll just show the status endpoint works
        logger.info("Background processing started. In production, you would:")
        logger.info("1. Return the API response immediately to the user")
        logger.info("2. Process the audio in the background")
        logger.info("3. Allow the user to check status via the /status endpoint")
    else:
        logger.warning("Failed to create and process call")
    
    # Test 3: Check processing status
    logger.info("\n=== Test 3: Check processing status ===")
    if processed_call:
        status = client.get_call_status(processed_call['call_id'])
        if status:
            logger.info(f"Status for {processed_call['call_id']}:")
            logger.info(f"  - Status: {status['status']}")
            logger.info(f"  - Message: {status['message']}")
            logger.info(f"  - Has processed data: {status['has_processed_data']}")
            logger.info(f"  - Audio in S3: {status['audio_in_s3']}")
            logger.info(f"  - Created: {status['created_at']}")
            logger.info(f"  - Updated: {status['updated_at']}")
    
    # Test 4: Process an existing call later
    logger.info("\n=== Test 4: Process existing call later ===")
    if created_call:
        logger.info(f"Processing existing call {created_call['call_id']}...")
        processing_result = client.process_existing_call(created_call['call_id'])
        if processing_result:
            logger.info(f"Processing result: {processing_result['status']}")
            logger.info(f"Message: {processing_result['message']}")
        else:
            logger.warning("Failed to process existing call (this is expected if audio URL doesn't exist)")
    
    # Test 5: List all calls
    logger.info("\n=== Test 5: List all calls ===")
    calls = client.list_calls(limit=5)
    if calls:
        logger.info(f"Found {len(calls)} calls:")
        for call in calls:
            logger.info(f"  - {call['call_id']}: created at {call['created_at']}")
            if call.get('processed_data'):
                logger.info(f"    (Processed with {len(call['processed_data'])} analysis fields)")
    else:
        logger.warning("No calls found or failed to list calls")
    
    # Test 6: Demonstrate status monitoring (simulated)
    logger.info("\n=== Test 6: Demonstrate status monitoring ===")
    logger.info("In a real application, you would:")
    logger.info("1. Create a call with process_immediately=True")
    logger.info("2. Get immediate response with status='processing'")
    logger.info("3. Poll the /status endpoint to monitor progress")
    logger.info("4. Get final status when processing completes")
    logger.info("5. Retrieve processed data and S3 URLs")
    
    logger.info("\n=== Example completed ===")
    logger.info("Key benefits of the new asynchronous approach:")
    logger.info("✅ API responds immediately after database write")
    logger.info("✅ Background processing doesn't block the response")
    logger.info("✅ Users can monitor progress via status endpoint")
    logger.info("✅ Same processing pipeline as Bolna integration")
    logger.info("✅ No external dependencies (pure asyncio)")


if __name__ == "__main__":
    main()
