"""S3 utility functions for audio file management."""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, BinaryIO
import logging
import requests
import tempfile
import os
from urllib.parse import urlparse
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class S3Manager:
    """Manages S3 operations for audio files."""
    
    def __init__(self):
        """Initialize S3 client with credentials from settings."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.bucket_name = settings.s3_bucket_name
    
    def download_and_upload_audio(self, audio_url: str, call_id: str, file_extension: str = None) -> Optional[tuple[str, str]]:
        """
        Download audio file from external URL and upload to S3.
        
        Args:
            audio_url: URL of the audio file to download
            call_id: Unique identifier for the call (used in S3 key)
            file_extension: File extension for the audio file (if None, will be detected from URL or file headers)
            
        Returns:
            Tuple of (S3 URL, detected file extension), or None if operation fails
        """
        try:
            logger.info(f"Downloading audio from {audio_url} for call {call_id}")
            
            # If no file extension provided, try to detect it from the URL
            if file_extension is None:
                file_extension = self._extract_file_extension_from_url(audio_url)
                logger.info(f"Detected file extension from URL: {file_extension}")
            
            # Download the audio file
            response = requests.get(audio_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create a temporary file to store the downloaded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                # Write the downloaded content to the temporary file
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                
                temp_file_path = temp_file.name
            
            try:
                # Now detect the actual format from file headers (more reliable)
                detected_extension = self._detect_audio_format_from_headers(temp_file_path)
                if detected_extension != file_extension:
                    logger.info(f"Format detection corrected extension from '{file_extension}' to '{detected_extension}'")
                    
                    # Rename the temp file to have the correct extension
                    old_extension = file_extension.split('.')[-1] if '.' in file_extension else file_extension
                    new_temp_file_path = temp_file_path.replace(f".{old_extension}", f".{detected_extension}")
                    os.rename(temp_file_path, new_temp_file_path)
                    temp_file_path = new_temp_file_path
                    file_extension = detected_extension
                    logger.info(f"Renamed temp file to: {temp_file_path}")
                
                # Generate S3 key with proper extension
                s3_key = f"calls/{call_id}/audio.{file_extension}"
                content_type = self._get_content_type(file_extension)
                
                logger.info(f"Uploading to S3 with key: {s3_key}, content type: {content_type}")
                
                # Upload to S3
                with open(temp_file_path, 'rb') as file_obj:
                    self.s3_client.upload_fileobj(
                        file_obj,
                        self.bucket_name,
                        s3_key,
                        ExtraArgs={
                            'ContentType': content_type,
                            'Metadata': {
                                'call_id': call_id,
                                'source_url': audio_url,
                                'uploaded_at': str(datetime.now()),
                                'detected_format': file_extension
                            }
                        }
                    )
                
                # Generate S3 URL
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
                logger.info(f"Successfully uploaded audio for call {call_id} to S3: {s3_url}")
                
                return s3_url
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download audio from {audio_url}: {e}")
            return None
        except ClientError as e:
            logger.error(f"Failed to upload audio to S3 for call {call_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing audio for call {call_id}: {e}")
            return None
    
    def _get_content_type(self, file_extension: str) -> str:
        """Get the appropriate content type for a file extension."""
        content_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4',
            'aac': 'audio/aac',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac'
        }
        return content_types.get(file_extension.lower(), 'audio/mpeg')
    
    def _detect_audio_format_from_headers(self, file_path: str) -> str:
        """Detect audio format by examining file headers."""
        try:
            with open(file_path, 'rb') as f:
                # Read first 16 bytes to examine file headers
                header = f.read(16)
                
                # Check for common audio file signatures
                if header.startswith(b'ID3') or header.startswith(b'\xff\xfb') or header.startswith(b'\xff\xf3'):
                    return 'mp3'
                elif header.startswith(b'RIFF') and header[8:12] == b'WAVE':
                    return 'wav'
                elif header.startswith(b'ftyp'):
                    # Check for MP4/AAC variants
                    ftype = header[4:8]
                    if ftype in [b'M4A ', b'M4B ', b'M4P ', b'M4V ']:
                        return 'm4a'
                    elif ftype == b'MP4 ':
                        return 'mp4'
                elif header.startswith(b'\xff\xf1') or header.startswith(b'\xff\xf9'):
                    return 'aac'
                elif header.startswith(b'OggS'):
                    return 'ogg'
                elif header.startswith(b'fLaC'):
                    return 'flac'
                
                logger.warning(f"Could not detect audio format from headers for {file_path}")
                return 'mp3'  # Default fallback
                
        except Exception as e:
            logger.error(f"Error detecting audio format from headers: {e}")
            return 'mp3'  # Default fallback
    
    def _extract_file_extension_from_url(self, url: str) -> str:
        """
        Safely extract file extension from a URL.
        
        Args:
            url: URL to extract extension from
            
        Returns:
            File extension (defaults to 'mp3' if extraction fails)
        """
        try:
            from urllib.parse import urlparse
            import os
            
            # Parse the URL to get the path component
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            # Get the filename from the path
            filename = os.path.basename(path)
            
            # Extract extension from filename
            if "." in filename:
                extension = filename.split(".")[-1].split("?")[0]
                # Validate that it's a reasonable audio extension
                if extension.lower() in ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'mp4']:
                    return extension.lower()
                else:
                    logger.warning(f"Invalid audio extension '{extension}' from URL, using default 'mp3'")
                    return 'mp3'
            else:
                logger.info(f"No file extension found in URL path '{path}', using default 'mp3'")
                return 'mp3'
                
        except Exception as e:
            logger.error(f"Error extracting file extension from URL {url}: {e}")
            return 'mp3'  # Default fallback
    
    def download_audio_file(self, s3_key: str) -> Optional[BinaryIO]:
        """
        Download audio file from S3.
        
        Args:
            s3_key: S3 key (path) of the audio file
            
        Returns:
            File-like object containing the audio data, or None if download fails
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body']
        except ClientError as e:
            logger.error(f"Error downloading file {s3_key}: {e}")
            return None
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return None
    
    def get_audio_file_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for downloading an audio file.
        
        Args:
            s3_key: S3 key (path) of the audio file
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string, or None if generation fails
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL for {s3_key}: {e}")
            return None
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return None
    
    def extract_s3_key_from_url(self, s3_url: str) -> Optional[str]:
        """
        Extract S3 key from a full S3 URL.
        
        Args:
            s3_url: Full S3 URL (e.g., https://bucket.s3.region.amazonaws.com/key)
            
        Returns:
            S3 key string, or None if extraction fails
        """
        try:
            # Handle different S3 URL formats
            if s3_url.startswith('s3://'):
                # s3://bucket/key format
                return s3_url.replace(f's3://{self.bucket_name}/', '', 1)
            elif 'amazonaws.com' in s3_url:
                # https://bucket.s3.region.amazonaws.com/key format
                return s3_url.split('amazonaws.com/')[-1]
            else:
                # Assume it's already a key
                return s3_url
        except Exception as e:
            logger.error(f"Error extracting S3 key from URL {s3_url}: {e}")
            return None
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: S3 key (path) of the file
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking file existence for {s3_key}: {e}")
            return False
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return False


# Global S3 manager instance
s3_manager = S3Manager()
