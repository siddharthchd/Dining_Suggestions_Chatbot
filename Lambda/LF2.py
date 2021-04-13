import boto3
import json
import logging
from boto3.dynamodb.conditions import Key, Attr
from botocore.vendored import requests
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
sqs = boto3.client("sqs")
            # , region_name="us-west-2"
            # aws_access_key_id=AWS_ACCESS_KEY_ID,
            # aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def getSQSMsg():
    
    # url = SQS.get_queue_url(QueueName='ConciergeSQS').get('QueueUrl')
    # logger.debug(str(url))
    #queue = sqs.get_queue_by_name(QueueName='ConciergeSQS')
    response = sqs.receive_message(
        QueueUrl= "https://sqs.us-west-2.amazonaws.com/775586410689/ConciergeSQS")

        # AttributeNames=[ 'SentTimestamp' ],
        # MaxNumberOfMessages=1,
        # MessageAttributeNames=[ 'All' ],
        # VisibilityTimeout=0,
        # WaitTimeSeconds=0 )
    logger.debug(response)
     
    try:
        message = response['Messages'][0]
        logger.debug('in try.....')
        if message is None:
            logger.debug("Empty message")
            return None
    except KeyError:
        logger.debug('in catch.....')
        logger.debug("No message in the queue")
        return None
    message = response['Messages'][0]
    sqs.delete_message(
            QueueUrl="https://sqs.us-west-2.amazonaws.com/775586410689/ConciergeSQS",

            ReceiptHandle=message['ReceiptHandle']
        )
    logger.debug('Received and deleted message: %s' % response)
    return message

def lambda_handler(event, context):
    
    """
        Query SQS to get the messages
        Store the relevant info, and pass it to the Elastic Search
    """
    
    message = getSQSMsg() #data will be a json object

    if message is None:
        #logger.debug("No cuisine or phoneNum key found in message")
        return
    # print('Message : ', message)
    cuisine = message["MessageAttributes"]["cuisine"]["StringValue"]
    location = message["MessageAttributes"]["location"]["StringValue"]
    time = message["MessageAttributes"]["time"]["StringValue"]
    numOfPeople = message["MessageAttributes"]["people"]["StringValue"]
    phoneNumber = message["MessageAttributes"]["phone"]["StringValue"]
    phoneNumber = "+1" + phoneNumber
    if not cuisine or not phoneNumber:
        #logger.debug("No Cuisine or PhoneNumber key found in message")
        return
    
    ###
    
    es_query = "https://search-chatbot-54zrwxt66hy2opaucfhib5hore.us-west-2.es.amazonaws.com/_search?q={cuisine}".format(
        cuisine=cuisine)
    esResponse = requests.get(es_query)
    data = json.loads(esResponse.content.decode('utf-8'))
    try:
        esData = data["hits"]["hits"]
    except KeyError:
        logger.debug("Error extracting hits from ES response")
    
    #extract bID from AWS ES
    ids = []
    for restaurant in esData:
        ids.append(restaurant["_source"]["bID"])
    
    messageToSend = 'Hello! Here are my {cuisine} restaurant suggestions in {location} for {numPeople} people, for {diningDate} at {diningTime}: '.format(
            cuisine=cuisine,
            location=location,
            numPeople=numOfPeople,
            diningDate=date,
            diningTime=time,
        )

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('restaurants-yelp')
    itr = 1
    for id in ids:
        if itr == 6:
            break
        response = table.scan(FilterExpression=Attr('id').eq(id))
        item = response['Items'][0]
        if response is None:
            continue
        restaurantMsg = '' + str(itr) + '. '
        name = item["name"]
        address = item["address"]
        restaurantMsg += name +', located at ' + address +'. '
        messageToSend += restaurantMsg
        itr += 1
        
    messageToSend += "Enjoy your meal!!"

    
    try:
        print('Connecting to SQS.....')
        client = boto3.client('sns', region_name= 'us-west-2')
        response = client.publish(
            PhoneNumber=phoneNumber,
            Message= messageToSend,
            MessageStructure='string'
        )
    except KeyError:
        logger.debug("Error sending ")
    logger.debug("response - %s",json.dumps(response) )
    logger.debug("Message = '%s' Phone Number = %s" % (messageToSend, phoneNumber))
    
    return {
        'statusCode': 200,
        'body': json.dumps("LF2 running succesfully")
    }