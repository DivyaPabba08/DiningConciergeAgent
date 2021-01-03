import json

with open("restaurants.json") as json_file:
	restaurant_list = json.load(json_file)

text_file = open("es.txt", "w")

for restaurant in restaurant_list:
	idText = str(restaurant['id'])
	cuiText = str(restaurant['cuisine'])
	text_file.write('{"index": { "_index": "restaurants", "_type": "Restaurant", "_id": "' + idText + '"}} \n')
	text_file.write('{"restaurantID": ' + '"' + idText + '", "cuisine": "' + cuiText + '"} \n')

text_file.close()
