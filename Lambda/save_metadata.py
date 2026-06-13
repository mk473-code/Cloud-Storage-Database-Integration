import json
import boto3
import uuid
import re
from datetime import datetime, timezone

s3       = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

BUCKET_NAME = 'manikanta-cloud-storage'
TABLE_NAME  = 'FileMetadata'

ALLOWED_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf', 'text/plain', 'text/csv',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/zip', 'application/octet-stream'
}

def sanitize_filename(name):
    """Remove all characters except safe ones, limit length."""
    return re.sub(r'[^\w.\-()\s]', '_', name).strip()[:200]

def sanitize_text(text):
    """Strip leading/trailing whitespace and cap length."""
    return str(text).strip()[:500]

def safe_file_type(file_type):
    """Return file_type only if it is in the allowed list, else use safe default."""
    if file_type and file_type in ALLOWED_TYPES:
        return file_type
    return 'application/octet-stream'

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin':  '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}

    try:
        body = json.loads(event['body'])

        # Sanitize all user input before touching any AWS service
        file_name   = sanitize_filename(body.get('fileName', ''))
        description = sanitize_text(body.get('description', ''))
        file_type   = safe_file_type(body.get('fileType', ''))

        if not file_name:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'fileName is required'})
            }

        file_id     = str(uuid.uuid4())
        # Use tz=timezone.utc — creates a timezone-aware datetime, avoids naive datetime issue
        upload_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        s3_key      = f"uploads/{file_id}/{file_name}"

        # Generate pre-signed URL — ContentType is signed in, browser must send the same value
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket':      BUCKET_NAME,
                'Key':         s3_key,
                'ContentType': file_type
            },
            ExpiresIn=300
        )

        file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

        # Write sanitized values to DynamoDB — no raw user input reaches the DB call
        dynamodb.Table(TABLE_NAME).put_item(Item={
            'fileId':      file_id,
            'fileName':    file_name,
            'description': description,
            'uploadDate':  upload_date,
            'fileUrl':     file_url,
            's3Key':       s3_key
        })

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message':      'Metadata saved successfully',
                'fileId':       file_id,
                'presignedUrl': presigned_url,
                'fileUrl':      file_url
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
