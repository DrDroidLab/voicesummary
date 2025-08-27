# Bolna API Call Fetcher Script

This script fetches call details from the Bolna API and stores them in your audio calls database table.

## Features

- Fetches latest calls from Bolna API using your API key
- Downloads audio files and uploads them to S3
- Stores call transcripts and metadata in your PostgreSQL database
- Handles duplicate calls gracefully
- Comprehensive logging and error handling

## Prerequisites

1. **Bolna API Key**: Get your API key from [Bolna Dashboard](https://platform.bolna.ai)
2. **PostgreSQL Database**: Your `voicesummary` database should be running
3. **AWS S3**: Configured S3 bucket for storing audio files
4. **Python Dependencies**: All required packages are in your `requirements.txt`

## Setup

1. **Copy the configuration template**:
   ```bash
   cp bolna_config.env .env.bolna
   ```

2. **Edit the configuration file** with your actual values:
   ```bash
   nano .env.bolna
   ```

3. **Set the required environment variables**:
   ```bash
   export BOLNA_API_KEY="your_actual_api_key"
   export DATABASE_URL="postgresql://username:password@localhost:5432/voicesummary"
   export AWS_ACCESS_KEY_ID="your_aws_access_key"
   export AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
   export AWS_REGION="us-east-1"
   export S3_BUCKET_NAME="your-s3-bucket-name"
   ```

   Or source the file:
   ```bash
   source .env.bolna
   ```

## Usage

### Basic Usage

Run the script directly:
```bash
python fetch_bolna_calls.py
```

### With Environment Variables

```bash
BOLNA_API_KEY="your_key" python fetch_bolna_calls.py
```

### Cron Job (Automated)

Add to your crontab to run every hour:
```bash
0 * * * * cd /path/to/voicesummary && source .env.bolna && python fetch_bolna_calls.py >> /var/log/bolna_fetcher.log 2>&1
```

## What the Script Does

1. **Fetches Latest Calls**: Gets the 10 most recent calls from Bolna API
2. **Downloads Audio**: Retrieves audio files for each call
3. **Uploads to S3**: Stores audio files in your S3 bucket
4. **Stores in Database**: Creates records in your `audio_calls` table
5. **Handles Duplicates**: Skips calls that already exist

## Database Schema

The script stores data in your existing `AudioCall` table:

- `call_id`: Unique identifier from Bolna
- `transcript`: JSON transcript data
- `audio_file_url`: S3 URL to the audio file
- `timestamp`: Call timestamp
- `created_at`/`updated_at`: Automatically managed

## API Endpoints Used

Based on [Bolna API documentation](https://docs.bolna.ai/api-reference/introduction):

- `GET /executions/calls` - List calls
- `GET /executions/calls/{id}` - Get call details
- `GET /executions/calls/{id}/transcript` - Get transcript
- `GET /executions/calls/{id}/audio` - Get audio file

## Error Handling

- **API Errors**: Logs and continues with next call
- **S3 Upload Failures**: Logs error and skips call
- **Database Errors**: Logs error and continues
- **Missing Data**: Skips calls with incomplete information

## Logging

The script provides detailed logging:
- Info level: Successful operations
- Warning level: Non-critical issues
- Error level: Critical failures

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `BOLNA_API_KEY` is set
2. **Database Connection**: Check `DATABASE_URL` format
3. **S3 Permissions**: Verify AWS credentials and bucket access
4. **API Rate Limits**: Bolna may have rate limiting

### Debug Mode

For more verbose logging, modify the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Notes

- Never commit your `.env.bolna` file to version control
- Use IAM roles with minimal required permissions for S3
- Rotate your Bolna API key regularly
- Monitor script execution logs for security issues

## Customization

### Change Call Limit

Modify the limit in the main function:
```python
calls = bolna_client.get_latest_calls(limit=20)  # Fetch 20 calls instead of 10
```

### Custom S3 Path

Modify the S3 key generation in `S3Manager.upload_audio_file`:
```python
s3_key = f"custom/path/{call_id}/audio.mp3"
```

### Additional Fields

Add more fields to the database by modifying the `call_data` dictionary in the main function.

## Support

For issues with:
- **Bolna API**: Check [Bolna Documentation](https://docs.bolna.ai/api-reference/introduction)
- **Script Errors**: Check logs and ensure all environment variables are set
- **Database Issues**: Verify your PostgreSQL connection and schema
