import json
import boto3

def lambda_handler(event, context):
    # TODO implement
    client = boto3.client('lex-runtime')
    lastUserMessage = event['messages']
    botMessage = "Something went wrong!! Please try again"
    
    if lastUserMessage is None or len(lastUserMessage) < 1:
        return {
            'statusCode': 200,
            'body': json.dumps(botMessage)
        }
    
    lastUserMessage = str(lastUserMessage[0]['unstructured']['text'])
    # Update the user id, so it is different for different user
    response = client.post_text(
        botName='ConciergeChatbot',
        botAlias='$LATEST',
        userId='userId',
        inputText=lastUserMessage)
    
    # if response['message'] is not None or len(response['message']) > 0:
    botMessage = response['message']
    
    # print("Bot message", botMessage)
    
    botResponse =  [{
        'type': 'unstructured',
        'unstructured': {
          'text': botMessage
        }
      }]
    return {
        'status' : 'success',
        'status_code' : 200,
        'messages' : botResponse,
        'headers' : {
            "Access-Control-Allow-Headers" : "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        }
    }
    
# import json
# import boto3
# import logging

# def lambda_handler(event, context):
#     client = boto3.client('lex-runtime')
    
    
#     response = client.post_text(
#         botName='ConciergeChatbot',
#         botAlias='$LATEST',
#         userId='userId',
#         inputText=event["message"])
#     return {
#         'statusCode': 200,
#         'body': response,
#         "headers": { 
#             "Access-Control-Allow-Origin": {
#                         "Access-Control-Allow-Headers" : "Content-Type",
#                         "Access-Control-Allow-Origin": "*",
#                         "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
#                 }
#         }
#     }