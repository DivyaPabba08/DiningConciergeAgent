import json
from datetime import *
import boto3

def lambda_handler(event, context):
    """
    This is LF0 lamda function intended to extract the chat from the chatbot and send it to lex.
    """
    #print(event)
    msg_text = event["messages"][0]["unstructured"]["text"]
    print(msg_text)
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName="DiningConcierge",
        botAlias="beta",
        userId='482767636171',
        sessionAttributes={
        },
        requestAttributes={
        },
        inputText= msg_text
        )
    #print(response)    
    return_msg = response['message']
    #print(return_msg)
    return {
        'statusCode': 200,
        'headers': { 
            "Access-Control-Allow-Origin": "*" 
        },
        'body': json.dumps(return_msg)
    }
