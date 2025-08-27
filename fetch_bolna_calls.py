#!/usr/bin/env python3
"""
Script to fetch call details from Bolna API and store them in the audio calls database.

Usage:
    python fetch_bolna_calls.py

Environment Variables Required:
    - BOLNA_API_KEY: Your Bolna API key
    - DATABASE_URL: PostgreSQL connection string
    - AWS_ACCESS_KEY_ID: AWS access key for S3
    - AWS_SECRET_ACCESS_KEY: AWS secret key for S3
    - AWS_REGION: AWS region (default: us-east-1)
    - S3_BUCKET_NAME: S3 bucket name for storing audio files
"""

import os
import sys
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bolna API configuration
BOLNA_API_BASE_URL = "https://api.bolna.ai"
BOLNA_API_ENDPOINTS = {
    "calls": "/agent/all",  # Try the agent endpoint first
    "call_details": "/agent/{call_id}",
    "transcript": "/agent/{call_id}/transcript",
    "audio": "/agent/{call_id}/audio"
}

class BolnaAPIClient:
    """Client for interacting with Bolna API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_latest_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch the latest calls from Bolna API."""
        try:
            url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['calls']}"
            params = {"limit": limit}
            
            logger.info(f"Fetching latest {limit} calls from Bolna API...")
            logger.info(f"Request URL: {url}")
            logger.info(f"Request headers: {self.headers}")
            
            response = requests.get(url, headers=self.headers, params=params)
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.error(f"API Response: {response.text}")
            
            response.raise_for_status()
            
            calls_data = response.json()
            logger.info(f"Successfully fetched {len(calls_data)} calls")
            return calls_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch calls from Bolna API: {e}")
            raise
    
    def get_call_details(self, call_id: str) -> Dict[str, Any]:
        """Fetch detailed information for a specific call."""
        try:
            url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['call_details'].format(call_id=call_id)}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch call details for {call_id}: {e}")
            raise
    
    def get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """Fetch transcript for a specific call."""
        try:
            url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['transcript'].format(call_id=call_id)}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch transcript for {call_id}: {e}")
            raise
    
    def get_call_audio_url(self, call_id: str) -> Optional[str]:
        """Get the audio file URL for a specific call."""
        try:
            url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['audio'].format(call_id=call_id)}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # The response might contain the audio file URL or direct audio data
            # This depends on how Bolna API provides audio files
            audio_data = response.json()
            
            # Extract audio URL from response (adjust based on actual API response structure)
            if isinstance(audio_data, dict) and 'audio_url' in audio_data:
                return audio_data['audio_url']
            elif isinstance(audio_data, dict) and 'url' in audio_data:
                return audio_data['url']
            else:
                logger.warning(f"Could not extract audio URL from response for call {call_id}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch audio for {call_id}: {e}")
            return None


class S3Manager:
    """Manager for S3 operations."""
    
    def __init__(self, access_key: str, secret_key: str, region: str, bucket_name: str):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        self.bucket_name = bucket_name
    
    def upload_audio_file(self, audio_url: str, call_id: str) -> str:
        """Download audio from URL and upload to S3, return S3 URL."""
        try:
            # Download audio file from the provided URL
            response = requests.get(audio_url, stream=True)
            response.raise_for_status()
            
            # Generate S3 key
            s3_key = f"calls/{call_id}/audio.mp3"
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                response.raw,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': 'audio/mpeg'}
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            logger.info(f"Successfully uploaded audio for call {call_id} to S3: {s3_url}")
            
            return s3_url
            
        except Exception as e:
            logger.error(f"Failed to upload audio for call {call_id}: {e}")
            raise


class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get database session."""
        return self.SessionLocal()
    
    def call_exists(self, call_id: str) -> bool:
        """Check if a call already exists in the database."""
        session = self.get_session()
        try:
            # Import here to avoid circular imports
            from app.models import AudioCall
            existing_call = session.query(AudioCall).filter(AudioCall.call_id == call_id).first()
            return existing_call is not None
        finally:
            session.close()
    
    def create_call(self, call_data: Dict[str, Any]) -> bool:
        """Create a new call record in the database."""
        session = self.get_session()
        try:
            # Import here to avoid circular imports
            from app.models import AudioCall
            
            # Convert timestamp if it's a string
            timestamp = call_data.get('timestamp')
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.utcnow()
            elif timestamp is None:
                timestamp = datetime.utcnow()
            
            db_call = AudioCall(
                call_id=call_data['call_id'],
                transcript=call_data['transcript'],
                audio_file_url=call_data['audio_file_url'],
                timestamp=timestamp
            )
            
            session.add(db_call)
            session.commit()
            session.refresh(db_call)
            
            logger.info(f"Successfully created call record for {call_data['call_id']}")
            return True
            
        except IntegrityError:
            session.rollback()
            logger.warning(f"Call {call_data['call_id']} already exists, skipping...")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create call record for {call_data['call_id']}: {e}")
            return False
        finally:
            session.close()


def main():
    """Main function to fetch and store Bolna calls."""
    # Check required environment variables
    required_env_vars = [
        'BOLNA_API_KEY',
        'DATABASE_URL',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'S3_BUCKET_NAME'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables and try again.")
        sys.exit(1)
    
    # Initialize clients
    try:
        bolna_client = BolnaAPIClient(os.getenv('BOLNA_API_KEY'))
        s3_manager = S3Manager(
            access_key=os.getenv('AWS_ACCESS_KEY_ID'),
            secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region=os.getenv('AWS_REGION', 'us-east-1'),
            bucket_name=os.getenv('S3_BUCKET_NAME')
        )
        db_manager = DatabaseManager(os.getenv('DATABASE_URL'))
        
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        sys.exit(1)
    
    try:
        # Fetch latest calls
        calls = bolna_client.get_latest_calls(limit=10)
        
        if not calls:
            logger.info("No calls found from Bolna API")
            return
        
        processed_count = 0
        skipped_count = 0
        
        for call in calls:
            call_id = call.get('id') or call.get('call_id')
            if not call_id:
                logger.warning("Call missing ID, skipping...")
                continue
            
            # Check if call already exists
            if db_manager.call_exists(call_id):
                logger.info(f"Call {call_id} already exists, skipping...")
                skipped_count += 1
                continue
            
            try:
                # Get detailed call information
                call_details = bolna_client.get_call_details(call_id)
                
                # Get transcript
                transcript = bolna_client.get_call_transcript(call_id)
                
                # Get audio URL
                audio_url = bolna_client.get_call_audio_url(call_id)
                
                if not audio_url:
                    logger.warning(f"No audio URL found for call {call_id}, skipping...")
                    skipped_count += 1
                    continue
                
                # Upload audio to S3
                s3_audio_url = s3_manager.upload_audio_file(audio_url, call_id)
                
                # Prepare call data for database
                call_data = {
                    'call_id': call_id,
                    'transcript': transcript,
                    'audio_file_url': s3_audio_url,
                    'timestamp': call_details.get('created_at') or call_details.get('timestamp')
                }
                
                # Store in database
                if db_manager.create_call(call_data):
                    processed_count += 1
                else:
                    skipped_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process call {call_id}: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"Processing complete. Processed: {processed_count}, Skipped: {skipped_count}")
        
    except Exception as e:
        logger.error(f"Failed to fetch and process calls: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
