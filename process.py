from app.utils.improved_voice_analyzer import ImprovedVoiceAnalyzer

def analyze_audio(audio_file_path):
    """Single function to analyze any audio file."""
    
    # Initialize analyzer
    analyzer = ImprovedVoiceAnalyzer(
        audio_path=audio_file_path,
        pause_sensitivity="normal"
    )
    
    # Single function call - does everything
    results = analyzer.analyze_conversation()
    
    return results

