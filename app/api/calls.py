"""API endpoints for managing audio calls."""

import logging
import os
import tempfile
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AudioCall
from app.schemas import AudioCallCreate, AudioCallCreateWithProcessing, AudioCallResponse, AudioCallUpdate, CallProcessingResponse, CallStatusResponse, AgentAnalysisRequest, AgentAnalysisResponse
from app.utils.s3 import s3_manager
from app.utils.audio_processor import process_audio_and_store
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.post("/", response_model=AudioCallResponse, status_code=status.HTTP_201_CREATED)
async def create_call(
    call_data: AudioCallCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new audio call record.
    
    Args:
        call_data: Call information including transcript and audio URL
        db: Database session
        
    Returns:
        Created call record
    """
    # Check if call_id already exists
    existing_call = db.query(AudioCall).filter(AudioCall.call_id == call_data.call_id).first()
    if existing_call:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Call with ID {call_data.call_id} already exists"
        )
    
    # Create new call record
    db_call = AudioCall(
        call_id=call_data.call_id,
        transcript=call_data.transcript,
        audio_file_url=call_data.audio_file_url,
        timestamp=call_data.timestamp or datetime.utcnow()
    )
    
    # Initialize processed_data
    if not db_call.processed_data:
        db_call.processed_data = {}
    
    # Generate transcript summary using OpenAI
    try:
        from app.utils.transcript_summarizer import summarize_transcript
        transcript_summary = summarize_transcript(
            transcript=call_data.transcript,
            call_context=call_data.call_context
        )
        
        if transcript_summary:
            db_call.processed_data['transcript_summary'] = transcript_summary
            logger.info(f"Transcript summary completed for call {call_data.call_id}")
        else:
            logger.warning(f"Transcript summary failed for call {call_data.call_id}")
            
    except Exception as e:
        logger.warning(f"Could not perform transcript summarization for call {call_data.call_id}: {e}")
        # Continue without transcript summary
    
    # If agent type is specified, perform agent analysis
    if call_data.agent_type:
        try:
            from app.utils.agent_analyzer import AgentAnalyzer
            analyzer = AgentAnalyzer()
            analysis_result = analyzer.analyze_agent_performance(
                transcript=call_data.transcript,
                agent_type=call_data.agent_type,
                call_context=call_data.call_context
            )
            
            if 'error' not in analysis_result:
                db_call.processed_data['agent_analysis'] = analysis_result
                logger.info(f"Agent analysis completed for call {call_data.call_id}")
            else:
                logger.warning(f"Agent analysis failed for call {call_data.call_id}: {analysis_result['error']}")
                
        except Exception as e:
            logger.warning(f"Could not perform agent analysis for call {call_data.call_id}: {e}")
            # Continue without agent analysis
    
    try:
        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        return db_call
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create call: {str(e)}"
        )


async def process_call_background(call_id: str, audio_url: str, transcript_data: Dict[str, Any], call_timestamp: datetime):
    """
    Background task to process a call asynchronously.
    
    This function runs in the background after the API response is sent.
    
    Args:
        call_id: Unique identifier for the call
        audio_url: URL of the audio file to process
        transcript_data: Transcript data to enhance
        call_timestamp: Timestamp of the call
    """
    try:
        logger.info(f"Starting background processing for call {call_id}")
        
        # Download audio file from external URL
        logger.info(f"Downloading audio from: {audio_url}")
        
        # Create temporary file for audio processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_audio_path = temp_file.name
        
        try:
            # Download audio file
            import requests
            response = requests.get(audio_url, stream=True)
            response.raise_for_status()
            
            # Save to temporary file
            with open(temp_audio_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded audio to temporary file: {temp_audio_path}")
            
            # Prepare S3 configuration
            s3_config = {
                'access_key': settings.aws_access_key_id,
                'secret_key': settings.aws_secret_access_key,
                'region': settings.aws_region,
                'bucket': settings.s3_bucket_name
            }
            
            # Process audio and store results using the same function as Bolna integration
            logger.info(f"Processing audio and transcript for call {call_id}")
            success, message = process_audio_and_store(
                audio_file_path=temp_audio_path,
                transcript_data=transcript_data,
                call_id=call_id,
                call_timestamp=call_timestamp,
                database_url=settings.database_url,
                s3_config=s3_config
            )
            
            if success:
                logger.info(f"Successfully processed call {call_id} in background: {message}")
            else:
                logger.error(f"Failed to process call {call_id} in background: {message}")
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                logger.info(f"Cleaned up temporary file: {temp_audio_path}")
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download audio for call {call_id} in background: {e}")
    except Exception as e:
        logger.error(f"Error processing call {call_id} in background: {e}")


@router.post("/create-and-process", response_model=CallProcessingResponse, status_code=status.HTTP_201_CREATED)
async def create_and_process_call(
    call_data: AudioCallCreateWithProcessing,
    db: Session = Depends(get_db)
):
    """
    Create a new audio call record and optionally process it in the background.
    
    This endpoint provides feature parity with the Bolna integration by:
    1. Creating the call record in the database (immediate)
    2. Returning response to API caller immediately
    3. If process_immediately is True, starting background processing:
       - Downloading the audio file from the provided URL
       - Processing the audio using the voice analyzer
       - Enhancing the transcript with accurate timestamps
       - Storing the processed data and uploading audio to S3
    
    Args:
        call_data: Call information with processing option
        db: Database session
        
    Returns:
        Processing status and results
    """
    # Check if call_id already exists
    existing_call = db.query(AudioCall).filter(AudioCall.call_id == call_data.call_id).first()
    if existing_call:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Call with ID {call_data.call_id} already exists"
        )
    
    try:
        # Create new call record
        db_call = AudioCall(
            call_id=call_data.call_id,
            transcript=call_data.transcript,
            audio_file_url=call_data.audio_file_url,
            timestamp=call_data.timestamp or datetime.utcnow()
        )
        
        # Initialize processed_data
        if not db_call.processed_data:
            db_call.processed_data = {}
        
        # Generate transcript summary using OpenAI
        try:
            from app.utils.transcript_summarizer import summarize_transcript
            transcript_summary = summarize_transcript(
                transcript=call_data.transcript,
                call_context=call_data.call_context
            )
            
            if transcript_summary:
                db_call.processed_data['transcript_summary'] = transcript_summary
                logger.info(f"Transcript summary completed for call {call_data.call_id}")
            else:
                logger.warning(f"Transcript summary failed for call {call_data.call_id}")
                
        except Exception as e:
            logger.warning(f"Could not perform transcript summarization for call {call_data.call_id}: {e}")
            # Continue without transcript summary
        
        # If agent type is specified, perform agent analysis
        if call_data.agent_type:
            try:
                from app.utils.agent_analyzer import AgentAnalyzer
                analyzer = AgentAnalyzer()
                analysis_result = analyzer.analyze_agent_performance(
                    transcript=call_data.transcript,
                    agent_type=call_data.agent_type,
                    call_context=call_data.call_context
                )
                
                if 'error' not in analysis_result:
                    db_call.processed_data['agent_analysis'] = analysis_result
                    logger.info(f"Agent analysis completed for call {call_data.call_id}")
                else:
                    logger.warning(f"Agent analysis failed for call {call_data.call_id}: {analysis_result['error']}")
                    
            except Exception as e:
                logger.warning(f"Could not perform agent analysis for call {call_data.call_id}: {e}")
                # Continue without agent analysis
        
        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        
        # If immediate processing is requested, start background processing
        if call_data.process_immediately:
            logger.info(f"Starting background processing for call {call_data.call_id}")
            
            # Start background processing task
            asyncio.create_task(
                process_call_background(
                    call_id=call_data.call_id,
                    audio_url=call_data.audio_file_url,
                    transcript_data=call_data.transcript,
                    call_timestamp=call_data.timestamp or datetime.utcnow()
                )
            )
            
            # Return immediately with processing status
            return CallProcessingResponse(
                status="processing",
                message="Call created successfully. Processing started in background.",
                call_id=call_data.call_id
            )
        else:
            # Return success without processing
            return CallProcessingResponse(
                status="created",
                message="Call created successfully. Use /{call_id}/process-full to process it.",
                call_id=call_data.call_id
            )
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create call {call_data.call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create call: {str(e)}"
        )


@router.get("/count")
async def get_calls_count(db: Session = Depends(get_db)):
    """
    Get total count of calls.
    
    Args:
        db: Database session
        
    Returns:
        Total count of calls
    """
    count = db.query(AudioCall).count()
    return {"total": count}


@router.get("/{call_id}", response_model=AudioCallResponse)
async def get_call(call_id: str, db: Session = Depends(get_db)):
    """
    Get call information by ID.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Call information
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    return call


@router.get("/{call_id}/audio")
async def download_audio(call_id: str, db: Session = Depends(get_db)):
    """
    Download audio file for a specific call.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Audio file as streaming response from S3
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Check if audio_file_url exists
    if not call.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audio file URL available for this call"
        )
    
    # Check if the URL is already an S3 URL
    if call.audio_file_url.startswith(f"https://{s3_manager.bucket_name}.s3.amazonaws.com/"):
        # Already an S3 URL, serve directly from S3
        s3_key = s3_manager.extract_s3_key_from_url(call.audio_file_url)
        if s3_key and s3_manager.file_exists(s3_key):
            audio_file = s3_manager.download_audio_file(s3_key)
            if audio_file:
                # Check if the S3 key has a file extension
                if '.' in s3_key:
                    # S3 key has extension - use it
                    file_extension = s3_key.split('.')[-1]
                    content_type = s3_manager._get_content_type(file_extension)
                else:
                    # S3 key has no extension - detect format from file content
                    logger.info(f"S3 key has no extension, detecting format from content: {s3_key}")
                    
                    # Read the file content to detect format
                    audio_content = audio_file.read()
                    
                    # Check if the content is actually an error message instead of audio
                    if len(audio_content) < 1000:  # Audio files are usually much larger
                        content_text = audio_content.decode('utf-8', errors='ignore')
                        if any(keyword in content_text.lower() for keyword in ['error', 'failed', 'detail', 'exception']):
                            logger.error(f"S3 object contains error message instead of audio: {content_text}")
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail="Audio file not available - processing failed"
                            )
                    
                    # Create a temporary file to analyze the format
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        temp_file.write(audio_content)
                        temp_file_path = temp_file.name
                    
                    try:
                        # Detect format from file headers
                        detected_extension = s3_manager._detect_audio_format_from_headers(temp_file_path)
                        logger.info(f"Detected audio format: {detected_extension}")
                        
                        file_extension = detected_extension
                        content_type = s3_manager._get_content_type(detected_extension)
                        
                        logger.info(f"Using detected format for serving: extension={file_extension}, content_type={content_type}")
                        
                    finally:
                        # Clean up temporary file
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                    
                    # Use the audio content we already read
                    audio_data = audio_content
                
                logger.info(f"Serving audio from S3 for call {call_id}: extension={file_extension}, content_type={content_type}")
                
                # Use the audio data we have (either from fresh read or from format detection)
                if 'audio_data' not in locals():
                    audio_data = audio_file.read()
                
                return Response(
                    content=audio_data,
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={call_id}.{file_extension}",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
    
    # If not an S3 URL or S3 file doesn't exist, download from external URL and upload to S3
    try:
        logger.info(f"Processing audio for call {call_id}: URL={call.audio_file_url}")
        
        # Download from external URL and upload to S3 (extension will be auto-detected)
        s3_url = s3_manager.download_and_upload_audio(call.audio_file_url, call_id)
        
        if s3_url:
            # Update the database with the new S3 URL
            call.audio_file_url = s3_url
            db.commit()
            
            # Extract the detected file extension from the S3 URL
            s3_key = s3_manager.extract_s3_key_from_url(s3_url)
            if s3_key and "." in s3_key:
                detected_extension = s3_key.split(".")[-1]
            else:
                detected_extension = "mp3"  # fallback
            
            # Serve the audio from S3
            audio_file = s3_manager.download_audio_file(s3_key)
            
            if audio_file:
                # Determine content type from detected file extension
                content_type = s3_manager._get_content_type(detected_extension)
                
                logger.info(f"Serving audio after S3 upload for call {call_id}: extension={detected_extension}, content_type={content_type}")
                
                return Response(
                    content=audio_file.read(),
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={call_id}.{detected_extension}",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to serve audio file from S3"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download and upload audio file to S3"
            )
            
    except Exception as e:
        logger.error(f"Error processing audio for call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio file: {str(e)}"
        )


@router.get("/{call_id}/transcript")
async def get_transcript(call_id: str, db: Session = Depends(get_db)):
    """
    Get transcript JSON for a specific call.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Transcript JSON data
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    return {"call_id": call_id, "transcript": call.transcript}


async def process_call_full_internal(call_id: str, db: Session) -> Dict[str, Any]:
    """
    Internal function to process a call completely.
    
    This is extracted from the public endpoint to allow reuse.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Processing results dictionary
    """
    # Get the call record
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Check if audio_file_url exists
    if not call.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file URL available for this call"
        )
    
    # Check if already fully processed
    if call.processed_data and call.audio_file_url.startswith(f"https://{s3_manager.bucket_name}.s3.amazonaws.com/"):
        return {
            "status": "already_processed",
            "message": "Call already fully processed with audio analysis and S3 storage",
            "call_id": call_id,
            "processed_data": call.processed_data,
            "s3_url": call.audio_file_url
        }
    
    try:
        logger.info(f"Starting full processing for call {call_id}")
        
        # Download audio file from external URL
        logger.info(f"Downloading audio from: {call.audio_file_url}")
        
        # Create temporary file for audio processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_audio_path = temp_file.name
        
        try:
            # Download audio file
            import requests
            response = requests.get(call.audio_file_url, stream=True)
            response.raise_for_status()
            
            # Save to temporary file
            with open(temp_audio_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded audio to temporary file: {temp_audio_path}")
            
            # Prepare S3 configuration
            s3_config = {
                'access_key': settings.aws_access_key_id,
                'secret_key': settings.aws_secret_access_key,
                'region': settings.aws_region,
                'bucket': settings.s3_bucket_name
            }
            
            # Process audio and store results using the same function as Bolna integration
            logger.info(f"Processing audio and transcript for call {call_id}")
            success, message = process_audio_and_store(
                audio_file_path=temp_audio_path,
                transcript_data=call.transcript,
                call_id=call_id,
                call_timestamp=call.timestamp,
                database_url=settings.database_url,
                s3_config=s3_config
            )
            
            if success:
                # Refresh the call record to get updated data
                db.refresh(call)
                
                logger.info(f"Successfully processed call {call_id}: {message}")
                
                return {
                    "status": "success",
                    "message": message,
                    "call_id": call_id,
                    "processed_data": call.processed_data,
                    "s3_url": call.audio_file_url
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to process audio: {message}"
                )
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                logger.info(f"Cleaned up temporary file: {temp_audio_path}")
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download audio for call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download audio file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process call: {str(e)}"
        )


@router.post("/{call_id}/process-full", response_model=CallProcessingResponse, status_code=status.HTTP_200_OK)
async def process_call_full(
    call_id: str,
    db: Session = Depends(get_db)
):
    """
    Process a call completely: download audio, analyze it, enhance transcript, and store results.
    
    This endpoint provides feature parity with the Bolna integration by:
    1. Downloading the audio file from the provided URL
    2. Processing the audio using the voice analyzer
    3. Enhancing the transcript with accurate timestamps
    4. Storing the processed data in the database
    5. Uploading the audio file to S3
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Processing status and results
    """
    result = await process_call_full_internal(call_id, db)
    return CallProcessingResponse(**result)


@router.post("/{call_id}/process-audio", status_code=status.HTTP_200_OK)
async def process_audio(call_id: str, db: Session = Depends(get_db)):
    """
    Process audio file for a specific call by downloading from external URL and uploading to S3.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Processing status and S3 URL if successful
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Check if audio_file_url exists
    if not call.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audio file URL available for this call"
        )
    
    # Check if already processed (S3 URL)
    if call.audio_file_url.startswith(f"https://{s3_manager.bucket_name}.s3.amazonaws.com/"):
        return {
            "status": "already_processed",
            "message": "Audio file already processed and stored in S3",
            "s3_url": call.audio_file_url
        }
    
    try:
        # Determine file extension from URL
        file_extension = "mp3"  # Default
        if "." in call.audio_file_url:
            file_extension = call.audio_file_url.split(".")[-1].split("?")[0]
        
        logger.info(f"Processing audio for call {call_id}: URL={call.audio_file_url}, detected_extension={file_extension}")
        
        # Download from external URL and upload to S3
        s3_url = s3_manager.download_and_upload_audio(call.audio_file_url, call_id, file_extension)
        
        if s3_url:
            # Update the database with the new S3 URL
            call.audio_file_url = s3_url
            db.commit()
            
            return {
                "status": "success",
                "message": "Audio file successfully processed and uploaded to S3",
                "s3_url": s3_url
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download and upload audio file to S3"
            )
            
    except Exception as e:
        logger.error(f"Error processing audio for call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio file: {str(e)}"
        )


@router.get("/{call_id}/status")
async def get_call_processing_status(call_id: str, db: Session = Depends(get_db)):
    """
    Get the processing status of a call.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Processing status information
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Determine processing status
    if call.processed_data and call.audio_file_url.startswith(f"https://{s3_manager.bucket_name}.s3.amazonaws.com/"):
        status = "completed"
        message = "Call has been fully processed with audio analysis and S3 storage"
    elif call.processed_data:
        status = "partially_processed"
        message = "Call has been processed but audio may not be in S3 yet"
    else:
        status = "pending"
        message = "Call is pending processing"
    
    return CallStatusResponse(
        call_id=call_id,
        status=status,
        message=message,
        has_processed_data=bool(call.processed_data),
        audio_in_s3=call.audio_file_url.startswith(f"https://{s3_manager.bucket_name}.s3.amazonaws.com/"),
        created_at=call.created_at.isoformat() if call.created_at else None,
        updated_at=call.updated_at.isoformat() if call.updated_at else None
    )


@router.get("/", response_model=List[AudioCallResponse])
async def list_calls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all calls with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of call records
    """
    # Order by created_at descending (newest first) and apply pagination
    calls = db.query(AudioCall).order_by(AudioCall.created_at.desc()).offset(skip).limit(limit).all()
    return calls


@router.put("/{call_id}", response_model=AudioCallResponse)
async def update_call(
    call_id: str,
    call_update: AudioCallUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing call record.
    
    Args:
        call_id: Unique identifier for the call
        call_update: Updated call information
        db: Database session
        
    Returns:
        Updated call record
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Update fields if provided
    update_data = call_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(call, field, value)
    
    try:
        db.commit()
        db.refresh(call)
        return call
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update call: {str(e)}"
        )


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(call_id: str, db: Session = Depends(get_db)):
    """
    Delete a call record.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    try:
        db.delete(call)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete call: {str(e)}"
        )



@router.post("/{call_id}/analyze-agent", response_model=AgentAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_agent_performance(
    call_id: str,
    analysis_request: AgentAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze agent performance for a specific call using OpenAI.
    
    Args:
        call_id: Unique identifier for the call
        analysis_request: Analysis request with agent type and context
        db: Database session
        
    Returns:
        Agent performance analysis results
    """
    # Get the call record
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Check if transcript exists
    if not call.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcript available for analysis"
        )
    
    try:
        # Import agent analyzer
        from app.utils.agent_analyzer import AgentAnalyzer
        
        # Initialize analyzer
        analyzer = AgentAnalyzer()
        
        # Perform analysis
        analysis_result = analyzer.analyze_agent_performance(
            transcript=call.transcript,
            agent_type=analysis_request.agent_type,
            call_context=analysis_request.call_context
        )
        
        # Check if analysis was successful
        if 'error' in analysis_result:
            return AgentAnalysisResponse(
                call_id=call_id,
                analysis_result=analysis_result,
                agent_type=analysis_result.get('metadata', {}).get('agent_type', 'unknown'),
                agent_name=analysis_result.get('metadata', {}).get('agent_name', 'Unknown'),
                analysis_timestamp=analysis_result.get('metadata', {}).get('analysis_timestamp', ''),
                model_used=analysis_result.get('metadata', {}).get('model_used', ''),
                success=False,
                error_message=analysis_result['error']
            )
        
        # Update the call's processed_data with agent analysis
        if not call.processed_data:
            call.processed_data = {}
        
        call.processed_data['agent_analysis'] = analysis_result
        db.commit()
        
        return AgentAnalysisResponse(
            call_id=call_id,
            analysis_result=analysis_result,
            agent_type=analysis_result.get('metadata', {}).get('agent_type', 'unknown'),
            agent_name=analysis_result.get('metadata', {}).get('agent_name', 'Unknown'),
            analysis_timestamp=analysis_result.get('metadata', {}).get('analysis_timestamp', ''),
            model_used=analysis_result.get('metadata', {}).get('model_used', ''),
            success=True,
            error_message=None
        )
        
    except Exception as e:
        logger.error(f"Error analyzing agent performance for call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze agent performance: {str(e)}"
        )
