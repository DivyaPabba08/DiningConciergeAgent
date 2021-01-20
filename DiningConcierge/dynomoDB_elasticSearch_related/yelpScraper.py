import requests
import json

# get your API_KEY on https://www.yelp.com/developers/v3/manage_app
API_KEY = 'AicEM3PxoqGWgae4GeKmVw41V0XBOLSmMA4fPmJWpQt8xlH7Q0jNmK0uzT6hUKkLiyKhW7frhP2OVacSlAa5UTp_Nu2wVMqlP7NOVA74Ajb3m_RzwgtavU_Kayl_X3Yx'

url = 'https://api.yelp.com/v3/businesses/search'
# headers contain API key
headers = {'Authorization': 'Bearer {}'.format(API_KEY)}
# business location
LOCATION = 'Manhattan'
# list to store results
tmp = []
business_id = []

for cuisine in ['american','chinese','indian','italian','japanese']:
	# terms we are searching for
	TERM = cuisine + ' restaurant'
	# search paramters
	for OFFSET in range(0, 1000, 50): # can change the upper limit to 1000 in the real run
		url_params = {
		'term': TERM,
		'location': LOCATION,
		'limit': 50,
		'offset': OFFSET}

	# call the api
		response = requests.request('GET', url, headers=headers, params=url_params)

	# Business ID, Name, Address, Coordinates, Number of Reviews, Rating, Zip Code
		for business in response.json()["businesses"]:
			if business['id'] not in business_id:
				business_id.append(business['id'])
				data = {}
				data['id'] = business['id'],
				data['cuisine'] = cuisine,
				data['name'] = business['name'],
				data['address'] = business['location']['address1'],
				data['latitude'] = business['coordinates']['latitude'],
				data['longitude'] = business['coordinates']['longitude'],
				data['review_count'] = business['review_count'],
				data['rating'] = business['rating'],
				data['zip_code'] = business['location']['zip_code']
				tmp.append(data)
			
ans = []
for dic in tmp:
	new = {}
	for key,value in dic.items():
		if key == 'zip_code':
			new[key] = value
		else:
			new[key] = value[0]
	ans.append(new)

with open('restaurants.json', 'w') as fp:
    json.dump(ans, fp, indent=4)
