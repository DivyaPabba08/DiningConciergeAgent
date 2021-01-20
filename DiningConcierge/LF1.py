"""
We referenced the documentation and coding example for a sample bot which manages reservations for hotel rooms and car rentals from aws website.
References:http://docs.aws.amazon.com/lex/latest/dg/getting-started.html and https://docs.aws.amazon.com/lex/latest/dg/ex-book-trip-create-bot.html.
"""

import json
import datetime
import time
import os
import dateutil.parser
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


def isvalid_city(city):
    valid_cities = ['new york', 'new york city', 'nyc']
    return city.lower() in valid_cities


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_cuisine(cuisine):
	valid_cuisines = ['chinese', 'japanese', 'american', 'italian', 'indian']
	return cuisine.lower() in valid_cuisines
	
def validate_requirement(slots):
    location = try_ex(lambda: slots['location'])
    cuisine = try_ex(lambda: slots['cuisine'])
    dining_date = try_ex(lambda: slots['dining_date'])
    email = try_ex(lambda: slots['email'])

    if location and not isvalid_city(location):
        return build_validation_result(
            False,
            'location',
            'We currently do not accept {} as a valid destination.  Can you try a different city?(New York may be)'.format(location)
        )

    if cuisine and not isvalid_cuisine(cuisine):
        return build_validation_result(
            False,
            'cuisine',
            'We currently do not accept {} as a valid cuisine.  Can you try a different cuisine?(Currently we support Chinese,Japanese,American,Italian and Indian)'.format(cuisine)
        ) 

    if dining_date:
        if not isvalid_date(dining_date):
            return build_validation_result(False, 'dining_date', 'I did not understand your date.  When would you like to have lunch/dinner?')
        if datetime.datetime.strptime(dining_date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'dining_date', 'Reservations must be scheduled at least one day in advance.  Can you try a different date?')

    if email and '@' not in email:
        return build_validation_result(
            False,
            'email',
            'Sorry, {} is not a valid email address. Please provide a valid email address.'.format(email)
        )

    return {'isValid': True}


""" --- Functions that control the bot's behavior --- """
def thank(intent_request):
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'You are welcome.'
        }
    )

def greet(intent_request):
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Hi! What can I do for you?'
        }
    )
    
def suggest_dining(intent_request):
    """
    Performs dialog management and fulfillment for finding a restaurant.

    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """

  
    location = try_ex(lambda: intent_request['currentIntent']['slots']['location'])
    cuisine = try_ex(lambda: intent_request['currentIntent']['slots']['cuisine'])
    number_people = try_ex(lambda: intent_request['currentIntent']['slots']['numberOfPeople'])
    dining_date = try_ex(lambda: intent_request['currentIntent']['slots']['dining_date'])
    dining_time = try_ex(lambda: intent_request['currentIntent']['slots']['dining_time'])
    email = try_ex(lambda: intent_request['currentIntent']['slots']['email'])


    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    suggestion = json.dumps({
        'location': location,
        'cuisine': cuisine,
        'number_people': number_people,
        'dining_date': dining_date,
        'dining_time': dining_time,
        'email': email
    })
    print("SUGGESTION: {}".format(suggestion))

    session_attributes['suggestion'] = suggestion

    if intent_request['invocationSource'] == 'DialogCodeHook':
        validation_result = validate_requirement(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots = intent_request['currentIntent']['slots']
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )


        session_attributes['suggestion'] = suggestion
        return delegate(session_attributes, intent_request['currentIntent']['slots'])

    logger.debug('suggested lunch/dinner under={}'.format(suggestion))


    # Send the requests from users to the SQS
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName = "requestqueue") # get the URL of SQS
    if location and cuisine and number_people and dining_date and dining_time and email:
        queue_response = queue.send_message(MessageBody = suggestion)
        print("SUCESSFULLY SENT TO SQS")
       


    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, I have placed your reservation. The suggestion list will be sent to your email address very soon. Please let me know if you have anymore questions.'
                       
        }
    )



# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return suggest_dining(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank(intent_request)
    elif intent_name == 'GreetingIntent':
        return greet(intent_request)
   
    raise Exception('Intent with name ' + intent_name + ' not supported')


    
# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, user request is assumed to be coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)

