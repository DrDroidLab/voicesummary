#!/usr/bin/env python3
"""
Comprehensive call audio analysis script.
Downloads audio for a specific call ID and analyzes it for:
- Pauses and agent delays
- Interruptions
- Call termination issues
- Conversation health metrics
"""

import os
import sys
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal
from app.utils.call_utils import get_call_audio_file, get_call_by_id, get_call_transcript
from app.utils.improved_voice_analyzer import ImprovedVoiceAnalyzer


def convert_numpy_types(obj):
    """Convert numpy types and datetime to JSON-serializable types."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    else:
        return obj


def download_and_analyze_call(call_id: str, output_dir: str = "analysis_results") -> Optional[Dict[str, Any]]:
    """
    Download audio file for a specific call ID and analyze it for voice issues.
    
    Args:
        call_id: The call ID to analyze
        output_dir: Directory to save analysis results
        
    Returns:
        Analysis results dictionary, or None if failed
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Create database session
    db = SessionLocal()
    
    try:
        print(f"🔍 Analyzing call ID: {call_id}")
        print("=" * 60)
        
        # First, get call information to verify it exists
        call = get_call_by_id(call_id, db)
        if not call:
            print(f"❌ Call with ID {call_id} not found in database")
            return None
        
        print(f"✅ Found call: {call.call_id}")
        print(f"   Audio URL: {call.audio_file_url}")
        print(f"   Timestamp: {call.timestamp}")
        
        # Check if transcript exists (optional)
        if call.transcript:
            print(f"📝 Transcript data available")
        else:
            print(f"⚠️  No transcript data - running audio-only analysis")
        
        # Download the audio file
        print("📥 Downloading audio file...")
        audio_file = get_call_audio_file(call_id, db)
        
        if not audio_file:
            print("❌ Failed to download audio file")
            return None
        
        # Determine file extension from the original URL
        original_url = call.audio_file_url
        if '.ogg' in original_url.lower():
            extension = '.ogg'
        elif '.mp3' in original_url.lower():
            extension = '.mp3'
        elif '.wav' in original_url.lower():
            extension = '.wav'
        else:
            extension = '.ogg'  # Default to .ogg
        
        # Create output filename for audio
        audio_filename = f"{call_id}{extension}"
        audio_path = Path(output_dir) / audio_filename
        
        # Save the audio file locally
        print(f"💾 Saving audio to: {audio_path}")
        with open(audio_path, 'wb') as f:
            f.write(audio_file.read())
        
        # Get file size
        file_size = audio_path.stat().st_size
        print(f"✅ Audio downloaded successfully!")
        print(f"   File size: {file_size:,} bytes")
        print(f"   Saved to: {audio_path.absolute()}")
        
        # Handle transcript data (optional)
        transcript_path = None
        if call.transcript:
            # Create transcript file path
            transcript_filename = f"{call_id}_transcript.json"
            transcript_path = Path(output_dir) / transcript_filename
            
            # Save transcript data to JSON file
            print(f"💾 Saving transcript to: {transcript_path}")
            with open(transcript_path, 'w', encoding='utf-8') as f:
                json.dump(call.transcript, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Transcript saved successfully!")
        else:
            print(f"ℹ️  No transcript to save - audio-only analysis")
        
        # Now run the voice analysis
        print("\n🎯 Running voice analysis...")
        print("-" * 40)
        
        try:
            # Initialize the improved voice analyzer
            analyzer = ImprovedVoiceAnalyzer(
                audio_path=str(audio_path),
                transcript_path=str(transcript_path) if transcript_path else None,
                sample_rate=16000,
                pause_sensitivity="high"  # Use high sensitivity to detect shorter pauses
            )
            
            # Run the analysis
            results = analyzer.analyze_conversation()
            
            # Print summary
            analyzer.print_summary(results)
            
            # Save detailed analysis results
            analysis_filename = f"{call_id}_analysis.json"
            analysis_path = Path(output_dir) / analysis_filename
            
            print(f"\n💾 Saving detailed analysis to: {analysis_path}")
            # Convert numpy types to JSON-serializable types
            json_safe_results = convert_numpy_types(results)
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(json_safe_results, f, indent=2, ensure_ascii=False)
            
            # Create visualization
            viz_filename = f"{call_id}_visualization.png"
            viz_path = Path(output_dir) / viz_filename
            
            print(f"📊 Creating visualization: {viz_path}")
            analyzer.visualize(results, save_path=str(viz_path))
            
            print(f"\n🎉 Analysis complete! Results saved to: {output_dir}")
            print(f"   Audio: {audio_path.name}")
            if transcript_path:
                print(f"   Transcript: {transcript_path.name}")
            print(f"   Analysis: {analysis_path.name}")
            print(f"   Visualization: {viz_path.name}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error during voice analysis: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    except Exception as e:
        print(f"❌ Error processing call: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        db.close()


def main():
    """Main function to run the call audio analysis."""
    # The call ID you specified
    call_id = "f2463be4-1d0d-481d-a333-95032a93ad62"
    
    print("🎵 Voice Summary Call Analysis")
    print("=" * 60)
    print("This script will:")
    print("1. Download the audio file for the specified call")
    print("2. Extract and save the transcript data")
    print("3. Run comprehensive voice analysis")
    print("4. Generate visualizations and reports")
    print("=" * 60)
    
    # Run the analysis
    results = download_and_analyze_call(call_id)
    
    if results:
        print(f"\n🎯 Analysis Results Summary:")
        print(f"   Audio Duration: {results['audio_info']['duration']:.2f}s")
        print(f"   Speech Time: {results['audio_info']['speech_time']:.2f}s ({results['audio_info']['speech_percentage']:.1f}%)")
        print(f"   Pauses: {results['summary']['pause_count']}")
        print(f"   Interruptions: {results['summary']['interruption_count']}")
        print(f"   Termination Issues: {results['summary']['termination_issues']}")
        
        # Show critical issues if any
        if results['pauses']:
            print(f"\n⚠️  PAUSES DETECTED:")
            for pause in results['pauses'][:3]:
                print(f"   {pause['duration']:.1f}s pause at {pause['start_time']:.1f}s")
        
        if results['termination']['issues']:
            print(f"\n⚠️  CALL TERMINATION ISSUES:")
            for issue in results['termination']['issues']:
                print(f"   {issue}")
        
        if results['interruptions']:
            print(f"\n⚠️  INTERRUPTIONS DETECTED:")
            print(f"   Total: {len(results['interruptions'])} energy spikes detected")
            high_confidence_interruptions = [i for i in results['interruptions'] if i['confidence'] > 0.8]
            if high_confidence_interruptions:
                print(f"   High confidence: {len(high_confidence_interruptions)} interruptions")
        
        print(f"\n📁 All results saved to: analysis_results/")
        print(f"   You can review the detailed JSON report and visualization PNG file.")
        
    else:
        print("\n💥 Analysis failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
