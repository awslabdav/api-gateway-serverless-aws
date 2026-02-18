import boto3, json, os
from uuid import uuid4

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'ItemsTable')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    print('Evento Recibido:', json.dumps(event))


    #API Gateway Lambda Proxy Integration
    http_method = event.get('httpMethod','')
    path = event.get('path', '')
    
    if http_method == 'POST' and path == '/items':
        return create_item(event, context)
    elif http_method == 'GET' and path.startswith('/items/'):
        return get_item(event)
    elif http_method == 'GET' and path == '/items':
        return list_items(event)
    else:
        return {
            'statusCode': 404,
            'headers':{'Content-Type':'application/json'},
            'body': json.dumps({'error': 'Ruta no encontrada'})
        }

def create_item(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        item_id = body.get('id', str(uuid4()))

        item = {
            'id': item_id,
            'data':body.get('data',{}),
            'created_at': context.aws_request_id,  #simplificado
        }

        table.put_item(Item=item)

        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Item creado', 'id': item_id})
        }
    except Exception as e:
        print('Error:', str(e))
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Error interno del servidor'})
        }

def get_item(event):
    try:
        if not event.get('pathParameters') or 'id' not in event['pathParameters']:
            return error_response('ID requerido', 400)
        else:   
            item_id = event['pathParameters']['id']
            
        response = table.get_item(Key={'id':item_id})
        
        if 'Item' not in response:
            return error_response('Item no encontrado', 404)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response['Item'])
        }
    except Exception as e:
        return error_response(str(e), 500)

def list_items(event):
    try:
        response = table.scan(Limit=10)
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'items': response.get('Items', [])})
        }
    except Exception as e:
        return error_response(str(e), 500)

def error_response(message, status_code=400):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }