# Audio Processing with Local File Copies

This document explains how the updated `fetch_bolna_calls_standalone.py` script now handles audio file processing with proper format detection and local file storage.

## Key Improvements

### 1. **Automatic Format Detection**
- The script now detects audio format from file headers (not just content-type)
- Supports MP3, WAV, M4A, AAC, OGG, and FLAC formats
- Automatically appends correct file extensions to S3 uploads

### 2. **Local File Storage**
- All processed audio files are saved locally in the `recordings/` directory
- Files are named with the call ID and correct extension (e.g., `6debe72a-c135-413a-90f5-268d182f2c29.mp3`)
- Local copies are preserved for testing and verification

### 3. **Enhanced Error Handling**
- Better detection of failed audio downloads
- Proper error logging and reporting
- No more placeholder error files in S3

### 4. **Transcript Normalization**
- Automatically handles both string and dictionary transcript formats from Bolna API
- Converts string transcripts to structured dictionary format
- Ensures database compatibility and frontend rendering
- Validates transcript structure before database insertion

## Usage

### Basic Usage
```bash
python fetch_bolna_calls_standalone.py
```

### Test Format Detection
```bash
python fetch_bolna_calls_standalone.py --test
```

## Directory Structure

After running the script, you'll have:

```
voicesummary/
├── recordings/                          # Local audio file copies
│   ├── call_id_1.mp3                   # MP3 files with correct extensions
│   ├── call_id_2.wav                   # WAV files with correct extensions
│   └── call_id_3.m4a                   # M4A files with correct extensions
├── fetch_bolna_calls_standalone.py     # Updated script
└── AUDIO_PROCESSING_README.md          # This file
```

## File Format Detection

The script detects audio formats by examining file headers:

- **MP3**: ID3 tags or MPEG sync bytes (`0xFF 0xFB`, `0xFF 0xF3`)
- **WAV**: RIFF header with WAVE identifier
- **M4A/MP4**: ftyp box with M4A/MP4 identifiers
- **AAC**: ADTS sync bytes (`0xFF 0xF1`, `0xFF 0xF9`)
- **OGG**: OggS header
- **FLAC**: fLaC identifier

## Transcript Normalization

The script now automatically handles transcript data format inconsistencies from the Bolna API:

### **Input Formats Supported**
- **String transcripts**: Raw text from Bolna API (e.g., "assistant: Hello\nuser: Hi")
- **Dictionary transcripts**: Already structured data
- **JSON strings**: JSON-formatted strings that can be parsed
- **Other types**: None, empty strings, lists (converted to structured format)

### **Output Format**
All transcripts are normalized to a consistent dictionary structure:
```json
{
  "turns": [
    {
      "timestamp": "2025-08-26T15:04:11",
      "role": "AGENT",
      "content": "Hello from Bolna"
    },
    {
      "timestamp": "2025-08-26T15:04:12",
      "role": "USER",
      "content": "hello"
    },
    {
      "timestamp": "2025-08-26T15:04:13",
      "role": "AGENT",
      "content": "Hello! Am I speaking with you? Is this a good time to talk?"
    }
  ],
  "format": "bolna_conversation",
  "metadata": {
    "source": "bolna_api",
    "processing_note": "Converted from Bolna string format to turns structure",
    "original_format": "assistant/user string",
    "total_turns": 3
  }
}
```

### **Input Format Conversion**
The script automatically converts from Bolna API format:
```
assistant: Hello from Bolna
user: hello
assistant: Hello! Am I speaking with you?
```

**To:**
- **AGENT** role for `assistant:` lines
- **USER** role for `user:` lines  
- **Timestamps** starting from call creation time, incrementing by 1 second per turn
- **Structured turns** with role, content, and timestamp

### **Benefits**
- **Database Compatibility**: Ensures transcripts match the expected JSON schema with turns structure
- **Frontend Rendering**: Consistent structure for UI components with role-based display
- **Error Prevention**: No more validation errors from mixed data types
- **Data Integrity**: Structured format preserves transcript information with timestamps
- **Role Identification**: Clear distinction between AGENT and USER interactions
- **Time Sequencing**: Proper chronological ordering of conversation turns

### **Testing Transcript Normalization**
```bash
# Test transcript normalization functionality
python fetch_bolna_calls_standalone.py --test-transcript
```

## Local File Management

### Automatic Cleanup
- Old recording files (>24 hours) are automatically cleaned up
- Prevents disk space issues from accumulating files

### File Information
The script logs detailed information about each file:
- File size in bytes
- Age in hours
- Detected format
- Local path

## Testing Local Files

Once you have local audio files, you can:

1. **Play them directly** using any audio player
2. **Verify the format** by checking the file extension
3. **Test the backend** by uploading them to S3 manually
4. **Debug format detection** using the `--test` flag

## Troubleshooting

### Common Issues

1. **"Audio data is too small"**
   - The original audio URL failed to download
   - Check the backend logs for download errors

2. **"Could not detect audio format"**
   - File headers don't match known audio signatures
   - File might be corrupted or in unsupported format

3. **Local files not created**
   - Check write permissions for the `recordings/` directory
   - Verify the script has access to create directories

4. **"Input should be a valid dictionary" (transcript validation error)**
   - Transcript data from Bolna API is in unexpected format
   - The normalization should handle this automatically
   - Check logs for normalization details

5. **Database insertion failures**
   - Transcript structure validation failed
   - Check that normalized transcript has required fields (`text`, `segments`)

### Debug Commands

```bash
# Test format detection
python fetch_bolna_calls_standalone.py --test

# Test transcript normalization
python fetch_bolna_calls_standalone.py --test-transcript

# Check local recordings
ls -la recordings/

# View script logs
python fetch_bolna_calls_standalone.py 2>&1 | tee processing.log
```

## Benefits

1. **No More Format Errors**: Proper extensions prevent browser decoding issues
2. **Local Testing**: You can test audio files before they go to S3
3. **Better Debugging**: Local copies help troubleshoot processing issues
4. **Format Verification**: Confirm detected formats match actual file types
5. **Backup Copies**: Local files serve as backups if S3 uploads fail

## Next Steps

After running the script:

1. **Check the `recordings/` directory** for local audio files
2. **Verify file extensions** match the detected formats
3. **Test audio playback** using local files
4. **Check S3 uploads** have correct extensions and content types
5. **Test the frontend** to ensure audio loads properly
