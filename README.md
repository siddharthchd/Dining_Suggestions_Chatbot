# **Dining Suggestions Chatbot**
 
The concierge chatbot for dining suggestions is a server-less, distributed, micro-service driven web-based application deployed and hosted on AWS. This web application was developed as part of the course project assignment for the course - Cloud Computing (CS-GY:9223, NYU Tandon) 
<br>
<br>
# Table of contents
* [Description](#description)
* [Technologies](#technologies)
* [Workflow](#workflow)
<br>
<br>

## Description
---
Driven by Natural Language, the chatbot is designed using AWS services in order to provide restaurant suggestions to the users based on their requirements such as the City, Time and Date of dining, Number of People and the preferred Cuisine type. The frontend for the application is hosted in an AWS S3 bucket which provides the user with an interface to interact with the chatbot. AWS LexBot is used to process text inputs by the user, the bot uses Yelp API to fetch relevant suggestions which are then sent to the user over a text message to the number provided by the user. 
<br>
<br>
![Chatbot Demo](https://github.com/siddharthchd/Dining_Suggestions_Chatbot/blob/main/images/chatbot_demo.png)
<br>
<br>
## Technologies
---
* Python
* Javascript
* HTML
* CSS
* AWS - Simple Storage Service (S3)
* AWS - API Gateway
* AWS - Lambda
* AWS - Lex
* AWS - Simple Queue Service (SQS)
* AWS - Simple Notification Service (SNS)
* AWS - ElasticSearch
* AWS - DynamoDB
* AWS - CloudWatch Events
* Yelp API
<br>
<br>

## Workflow
---
* The frontend for the application (base code as displayed in image is present in the assets dir) is hostend in an S3 bucket as a static website.
* The 'swagger.yaml' file is used as a template for API Gateway. A lambda function (LF0) is invoked for all API requests.
* A different lambda function (LF1) is used as a code hook for the Lex Service.
* Yelp API is used to collect 7,000+ restaurants in belonging to 7 different cuisines.
* All the restaurant details are stored in DynamoDB which are indexed by their partial details stored in the ElasticSearch index.
* All messages are pushed to the SQS queue with the help of a queue worker lambda function (LF2) which is used to get random restaurant suggestions and then send the suggestions to the user using SNS.
* CloudWatch event trigger is used to invoke the lambda function every minute.

The following is the architecture for this project, to understand the workflow:-
![Chatbot Architecture](https://github.com/siddharthchd/Dining_Suggestions_Chatbot/blob/main/images/chatbot_architecture.png)
