"""
References:
https://aws.amazon.com/premiumsupport/knowledge-center/lambda-send-email-ses/
https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.Python.03.html
https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/search-example.html
"""
from __future__ import print_function

import os
import json
import boto3
from botocore.vendored import requests
from botocore.exceptions import ClientError
import random
import logging


ES_HOST = 'https://search-yelp-nyc-otn4hvekofuizu3y6tfcpdarwq.us-east-1.es.amazonaws.com/'
ES_INDEX = 'restaurants'
ES_TYPE = 'Restaurant'
ACCESS_KEY = ''
SECRET_ACCESS_KEY = ''
REGION = 'us-east-1'
URL = ES_HOST + ES_INDEX + '/' + ES_TYPE + '/_search'
SQS_URL = 'https://sqs.us-east-1.amazonaws.com/184124149104/requestqueue'
SENDER = 'dp3060@columbia.edu'


logger = logging.getLogger()

def lambda_handler(event, context):

    headers = { "Content-Type": "application/json" }

    sqs = boto3.client('sqs')
    receipt_handle = event["Records"][0]["receiptHandle"]
    for record in event["Records"]:
        req = json.loads(record["body"])
          
    # build the HTTP request
    url = URL + '?q=' + req["cuisine"].lower()
    restaurants_all= requests.get(url, headers=headers).json()["hits"]["hits"]
    
    
    # get the restaurant recommendation from ElasticSearch
    restaurants = random.sample(restaurants_all, 3) 
   
    # fetch detailed information from DynamoDB for the corresponding restaurants
    reservation = search_dynamodb(restaurants, req)

	#send text confirmation by SES
    email = str(req["email"])

    # send SES message
    ses = boto3.client('ses', region_name=REGION)

	#sending email
    message = ses.send_email(
        Source=SENDER,
        Destination={
            'ToAddresses': [email]
        },
        Message={
            'Body': {
                'Text': {
                    'Data': reservation
                }
            },
            'Subject': {
                'Data': 'Restaurant Suggestions from the Dining Concierge Chatbot'
            }
        }
    )

    # delete the sent req from SQS
    sqs.delete_message(
        QueueUrl=SQS_URL,
        ReceiptHandle=receipt_handle
    )
    return {
        'statusCode': 200,
        'headers': { 
            "Access-Control-Allow-Origin": "*" 
        },
        'body': json.dumps(reservation)
    }


def search_dynamodb(restaurants, req):
    dynamodb = boto3.client('dynamodb')
    
    cuisine = req["cuisine"].lower()
    rest_dic, name_list = {}, []

    for item in restaurants:
        print("item:",item)
        rest_id = item["_source"]["restaurantID"]
        rest_cuisine = item["_source"]["cuisine"]
        
        response = dynamodb.get_item(
            TableName='yelp-restaurants',
            Key={
                'cuisine': {
                    'S': cuisine
                },
                'id': {
                    'S': rest_id
                }
            }
        )
        rest_name=response["Item"]["name"]["S"]
        address= response["Item"]["address"]["S"]
        #review=response["Item"]["rating"]["N"]
        #zipcode=response["Item"]["zip_code"]["N"]
        #cuisine=response["Item"]["cuisine"]["S"]
        print(address,"address")
        
        if rest_name not in rest_dic:
            rest_dic[rest_name] = address
        
    cuisine=req["cuisine"]
    number_people = req["number_people"]
    dining_date = req["dining_date"]
    dining_time = req["dining_time"]
    location = req["location"]
    email = req["email"]

    for name in rest_dic:
        name_list.append(name)
    

    reservation = 'Hi! Here are our {} restaurant suggestions for {} people, on {}, {} at {}: (1). {} located at {} (2). {} located at {} (3). {} located at {}. Enjoy your meal!'.format(cuisine, number_people, dining_date, dining_time, location, name_list[0], rest_dic[name_list[0]], name_list[1], rest_dic[name_list[1]], name_list[2], rest_dic[name_list[2]])
    return reservation



