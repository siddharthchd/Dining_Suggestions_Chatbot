import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
SQS = boto3.client("sqs")

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

def getQueueURL():
    """Retrieve the URL for the configured queue name"""
    q = SQS.get_queue_url(QueueName='ConciergeSQS').get('QueueUrl')
    return q
    
def record(event):
    """The lambda handler"""
    logger.debug("Recording with event %s", event)
    data = event.get('data')
    try:
        logger.debug("Recording %s", data)
        u = getQueueURL()
        logging.debug("Got queue URL %s", u)
        resp = SQS.send_message(
            QueueUrl=u, 
            MessageBody="Dining Concierge message from LF1 ",
            MessageAttributes={
                "location": {
                    "StringValue": str(get_slots(event)["location"]),
                    "DataType": "String"
                },
                "cuisine": {
                    "StringValue": str(get_slots(event)["cuisine"]),
                    "DataType": "String"
                },
                "time" : {
                    "StringValue": str(get_slots(event)["time"]),
                    "DataType": "String"
                },
                "people" : {
                    "StringValue": str(get_slots(event)["people"]),
                    "DataType": "String"
                },
                "phone" : {
                    "StringValue": str(get_slots(event)["phone"]),
                    "DataType": "String"
                }
            }
        )
        logger.debug("Send result: %s", resp)
    except Exception as e:
        raise Exception("Could not record link! %s" % e)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


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


""" --- Helper Functions --- """

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
            'message': {'contentType': 'PlainText', 'content': message_content}
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_dining_suggestion(location, cuisine, time, people, phone):
    locations = ['manhattan', 'new york', 'nyc', 'new york city', 'ny']
    if location is not None and location.lower() not in locations:
        print('location')
        return build_validation_result(False,
                                       'location',
                                       'We do not have suggestions for "{}", try a different city'.format(location))
                                       
    cuisines = ['chinese', 'indian', 'italian', 'japanese', 'mexican', 'thai', 'korean', 'arab', 'american']
    if cuisine is not None and cuisine.lower() not in cuisines:
        return build_validation_result(False,
                                       'cuisine',
                                       'We do not have suggestions for {}, would you like suggestions for a differenet cuisine ?'.format(cuisine))

    
    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'time', None)

        hour, minute = time.split(':')
        hour = int(hour)
        minute = int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'time', None)

        if hour < 10 or hour > 23:
            # Outside of business hours
            return build_validation_result(False, 'time', 'Our business hours are from 10 AM. to 11 PM. Can you specify a time during this range?')
    
    if people is not None:
        people = int(people)
        if people < 1 or people > 15:
            return build_validation_result(False, 'people', 'Sorry! We accept reservations only upto 15 people')
    
    if phone is not None:
        if len(phone) != 10:
            return build_validation_result(False, 'phone', 'You have entered an invalid phone number. Please enter a valid 10 digit phone number.')  
    
    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def diningSuggestions(intent_request):
    
    location = get_slots(intent_request)["location"]
    cuisine = get_slots(intent_request)["cuisine"]
    time = get_slots(intent_request)["time"]
    people = get_slots(intent_request)["people"]
    phone = get_slots(intent_request)["phone"]
    
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_dining_suggestion(location, cuisine, time, people, phone)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

    
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        return delegate(output_session_attributes, get_slots(intent_request))

    record(intent_request)
    #print("SQS messageID:"+str(response['MessageId']))
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thank you for providing the information. Expect restaurant suggestions on your phone number {} shortly'.format(phone)})


""" --- Intents --- """

def welcome(intent_request):
    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "SSML",
                "content": "Hey! What can I do for you today?"
            },
        }
    }

def thankYou(intent_request):
    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "SSML",
                "content": "Thank you and visit again!"
            },
        }
    }


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    #logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return diningSuggestions(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thankYou(intent_request)
    elif intent_name == 'GreetingIntent':
        return welcome(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    # os.environ['TZ'] = 'America/New_York'
    # time.tzset()
    print(event)
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)