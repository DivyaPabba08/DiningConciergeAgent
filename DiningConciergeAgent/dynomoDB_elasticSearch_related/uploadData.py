from decimal import Decimal
import json
import boto3
import datetime

if __name__ == '__main__':

	dynamodb = boto3.resource('dynamodb',region_name='us-east-1') 
	table = dynamodb.Table('yelp-restaurants')

	with open("restaurants.json") as json_file:
		restaurant_list = json.load(json_file, parse_float=Decimal)

	for restaurant in restaurant_list:
		current_timestamp = datetime.datetime.now().isoformat()
		restaurant['insertedAtTimestamp'] = current_timestamp
		table.put_item(Item=restaurant)
