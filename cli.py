#!/usr/bin/env python3
"""
Voice Summary CLI Tool
Allows you to call utility functions from the shell with proper database session management.

Usage:
    python cli.py get-call <call_id>
    python cli.py get-transcript <call_id>
    python cli.py get-audio-url <call_id>
    python cli.py list-calls [--limit N]
    python cli.py create-call <call_id> <transcript_json> <audio_url>
    python cli.py --help
"""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app.utils.call_utils import (
    get_call_by_id,
    get_call_transcript,
    get_call_audio_file,
    get_call_audio_url,
    get_call_summary,
    validate_audio_file_exists
)
from app.models import AudioCall
from app.schemas import AudioCallCreate
from datetime import datetime


def get_db_session():
    """Get a database session."""
    return SessionLocal()


def print_call_info(call):
    """Print call information in a formatted way."""
    if not call:
        print("❌ Call not found")
        return
    
    print(f"\n📞 Call Information for: {call.call_id}")
    print("=" * 50)
    print(f"🕒 Timestamp: {call.timestamp}")
    print(f"📝 Audio URL: {call.audio_file_url}")
    print(f"📅 Created: {call.created_at}")
    print(f"🔄 Updated: {call.updated_at}")
    
    # Print transcript summary
    if call.transcript:
        print(f"\n📋 Transcript Summary:")
        if isinstance(call.transcript, dict):
            participants = call.transcript.get('participants', [])
            summary = call.transcript.get('summary', 'No summary')
            duration = call.transcript.get('duration', 'Unknown')
            
            print(f"   👥 Participants: {', '.join(participants)}")
            print(f"   ⏱️  Duration: {duration}")
            print(f"   📝 Summary: {summary}")
        else:
            print(f"   📄 Raw transcript: {call.transcript}")


def cmd_get_call(call_id: str):
    """Get call information by ID."""
    db = get_db_session()
    try:
        call = get_call_by_id(call_id, db)
        print_call_info(call)
    finally:
        db.close()


def cmd_get_transcript(call_id: str):
    """Get transcript for a call."""
    db = get_db_session()
    try:
        transcript = get_call_transcript(call_id, db)
        if transcript:
            print(f"\n📋 Transcript for call: {call_id}")
            print("=" * 50)
            print(json.dumps(transcript, indent=2, default=str))
        else:
            print(f"❌ No transcript found for call: {call_id}")
    finally:
        db.close()


def cmd_get_audio_url(call_id: str):
    """Get presigned audio URL for a call."""
    db = get_db_session()
    try:
        audio_url = get_call_audio_url(call_id, db)
        if audio_url:
            print(f"\n🎵 Audio URL for call: {call_id}")
            print("=" * 50)
            print(f"🔗 URL: {audio_url}")
        else:
            print(f"❌ No audio URL found for call: {call_id}")
    finally:
        db.close()


def cmd_get_call_summary(call_id: str):
    """Get comprehensive call summary."""
    db = get_db_session()
    try:
        summary = get_call_summary(call_id, db)
        if summary:
            print(f"\n📊 Call Summary for: {call_id}")
            print("=" * 50)
            print(json.dumps(summary, indent=2, default=str))
        else:
            print(f"❌ No summary found for call: {call_id}")
    finally:
        db.close()


def cmd_list_calls(limit: int = 10):
    """List all calls with pagination."""
    db = get_db_session()
    try:
        calls = db.query(AudioCall).limit(limit).all()
        print(f"\n📋 Found {len(calls)} calls (limit: {limit})")
        print("=" * 50)
        
        for i, call in enumerate(calls, 1):
            print(f"{i}. {call.call_id}")
            print(f"   📅 {call.timestamp}")
            print(f"   🎵 {call.audio_file_url}")
            if call.transcript and isinstance(call.transcript, dict):
                summary = call.transcript.get('summary', 'No summary')
                print(f"   📝 {summary[:50]}...")
            print()
    finally:
        db.close()


def cmd_create_call(call_id: str, transcript_json: str, audio_url: str):
    """Create a new call record."""
    db = get_db_session()
    try:
        # Parse transcript JSON
        try:
            transcript = json.loads(transcript_json)
        except json.JSONDecodeError:
            print("❌ Invalid JSON format for transcript")
            return
        
        # Check if call already exists
        existing_call = get_call_by_id(call_id, db)
        if existing_call:
            print(f"❌ Call with ID {call_id} already exists")
            return
        
        # Validate audio file exists in S3
        if not validate_audio_file_exists(audio_url):
            print(f"❌ Audio file not found in S3: {audio_url}")
            return
        
        # Create call data
        call_data = AudioCallCreate(
            call_id=call_id,
            transcript=transcript,
            audio_file_url=audio_url,
            timestamp=datetime.utcnow()
        )
        
        # Create call record
        db_call = AudioCall(
            call_id=call_data.call_id,
            transcript=call_data.transcript,
            audio_file_url=call_data.audio_file_url,
            timestamp=call_data.timestamp
        )
        
        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        
        print(f"✅ Successfully created call: {call_id}")
        print_call_info(db_call)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating call: {e}")
    finally:
        db.close()


def cmd_validate_audio(audio_url: str):
    """Validate if an audio file exists in S3."""
    exists = validate_audio_file_exists(audio_url)
    if exists:
        print(f"✅ Audio file exists: {audio_url}")
    else:
        print(f"❌ Audio file not found: {audio_url}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Voice Summary CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py get-call call_001_20241201
  python cli.py get-transcript call_001_20241201
  python cli.py get-audio-url call_001_20241201
  python cli.py list-calls --limit 5
  python cli.py create-call test_001 '{"participants": ["John"], "summary": "Test call"}' s3://bucket/test.mp3
  python cli.py validate-audio s3://bucket/test.mp3
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Get call command
    get_call_parser = subparsers.add_parser('get-call', help='Get call information by ID')
    get_call_parser.add_argument('call_id', help='Call ID to retrieve')
    
    # Get transcript command
    get_transcript_parser = subparsers.add_parser('get-transcript', help='Get transcript for a call')
    get_transcript_parser.add_argument('call_id', help='Call ID to get transcript for')
    
    # Get audio URL command
    get_audio_url_parser = subparsers.add_parser('get-audio-url', help='Get presigned audio URL for a call')
    get_audio_url_parser.add_argument('call_id', help='Call ID to get audio URL for')
    
    # Get call summary command
    get_summary_parser = subparsers.add_parser('get-summary', help='Get comprehensive call summary')
    get_summary_parser.add_argument('call_id', help='Call ID to get summary for')
    
    # List calls command
    list_calls_parser = subparsers.add_parser('list-calls', help='List all calls with pagination')
    list_calls_parser.add_argument('--limit', type=int, default=10, help='Maximum number of calls to list')
    
    # Create call command
    create_call_parser = subparsers.add_parser('create-call', help='Create a new call record')
    create_call_parser.add_argument('call_id', help='Unique call ID')
    create_call_parser.add_argument('transcript_json', help='Transcript as JSON string')
    create_call_parser.add_argument('audio_url', help='S3 URL for the audio file')
    
    # Validate audio command
    validate_audio_parser = subparsers.add_parser('validate-audio', help='Validate if audio file exists in S3')
    validate_audio_parser.add_argument('audio_url', help='S3 URL to validate')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'get-call':
            cmd_get_call(args.call_id)
        elif args.command == 'get-transcript':
            cmd_get_transcript(args.call_id)
        elif args.command == 'get-audio-url':
            cmd_get_audio_url(args.call_id)
        elif args.command == 'get-summary':
            cmd_get_call_summary(args.call_id)
        elif args.command == 'list-calls':
            cmd_list_calls(args.limit)
        elif args.command == 'create-call':
            cmd_create_call(args.call_id, args.transcript_json, args.audio_url)
        elif args.command == 'validate-audio':
            cmd_validate_audio(args.audio_url)
        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⏹️  Operation interrupted by user.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
