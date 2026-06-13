import json
import boto3

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'FileMetadata'              # DynamoDB table name

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}

    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.scan()
        items = response.get('Items', [])

        # Sort newest first
        items.sort(key=lambda x: x.get('uploadDate', ''), reverse=True)

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'files': items})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
