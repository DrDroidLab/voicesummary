#!/usr/bin/env python3
"""
Voice Summary Interactive Shell
Provides an interactive Python shell with database session and utility functions pre-loaded.

Usage:
    python shell.py
"""

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
import json

def get_db():
    """Get a database session."""
    return SessionLocal()

def print_help():
    """Print available functions and examples."""
    print("""
🎯 Voice Summary Interactive Shell
================================

📚 Available Functions:
----------------------
• get_db()                    - Get a fresh database session
• get_call_by_id(call_id, db) - Get call by ID
• get_call_transcript(call_id, db) - Get transcript for a call
• get_call_audio_url(call_id, db) - Get presigned audio URL
• get_call_summary(call_id, db) - Get comprehensive call summary
• validate_audio_file_exists(audio_url) - Check if audio file exists in S3

📋 Database Models:
------------------
• AudioCall                   - Audio call model
• AudioCallCreate            - Call creation schema

🔧 Examples:
-----------
# Get a database session
db = get_db()

# Get a call by ID
call = get_call_by_id("call_001", db)

# Get transcript
transcript = get_call_transcript("call_001", db)

# List all calls
calls = db.query(AudioCall).all()

# Don't forget to close the session when done!
db.close()

💡 Tips:
--------
• Always close your database session with db.close()
• Use db.commit() after making changes
• Use db.rollback() if something goes wrong
• Check the models and schemas for available fields

🚀 Ready to explore! Type 'help()' for Python help or 'print_help()' for this info.
""")

if __name__ == "__main__":
    print_help()
    
    # Import and start interactive shell
    try:
        import code
        # Create a local namespace with our functions
        local_vars = {
            'get_db': get_db,
            'get_call_by_id': get_call_by_id,
            'get_call_transcript': get_call_transcript,
            'get_call_audio_file': get_call_audio_file,
            'get_call_audio_url': get_call_audio_url,
            'get_call_summary': get_call_summary,
            'validate_audio_file_exists': validate_audio_file_exists,
            'AudioCall': AudioCall,
            'AudioCallCreate': AudioCallCreate,
            'datetime': datetime,
            'json': json,
            'print_help': print_help
        }
        
        # Start interactive shell
        code.interact(local=local_vars, banner="🎯 Voice Summary Interactive Shell\nType 'print_help()' for available functions")
        
    except ImportError:
        print("❌ Could not import 'code' module. Starting basic shell...")
        print("💡 You can still use the functions, but you'll need to import them manually.")
        print("🔧 Try: from app.utils.call_utils import get_call_by_id")
        
        # Fallback to basic shell
        import subprocess
        subprocess.run([sys.executable, "-i"])
