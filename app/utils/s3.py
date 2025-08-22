"""S3 utility functions for audio file management."""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, BinaryIO
import logging

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
                # Extract everything after the domain
                domain_part = f"{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com"
                if domain_part in s3_url:
                    key_part = s3_url.split(domain_part)[1]
                    # Remove leading slash and return the key
                    return key_part.lstrip('/')
                else:
                    # Fallback: try to extract from any amazonaws.com URL
                    parts = s3_url.split('amazonaws.com/')
                    if len(parts) > 1:
                        return parts[1]
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
