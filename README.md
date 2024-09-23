# Stock Market Report System
This system fetches stock market data, generates analysis reports, and sends them to users via email on a daily basis.
Architecture Overview
Show Image
Components

Alpha Vantage API: Source of stock market data.
Python Script:

Fetches stock data from Alpha Vantage
Retrieves user email addresses from DynamoDB
Generates HTML report


Docker: Contains the Python script and its dependencies.
Amazon ECR: Hosts the Docker image.
AWS Lambda: Runs the Docker image.
Amazon EventBridge: Triggers the Lambda function daily at 8 AM ET.
Amazon DynamoDB: Stores user email addresses.
Amazon SES: Sends email notifications with HTML reports.
Amazon CloudWatch: Logs metrics and monitors the system.

Workflow

EventBridge triggers the Lambda function every morning at 8 AM ET.
Lambda runs the Docker image containing the Python script.
The script fetches stock data from Alpha Vantage API.
User email addresses are retrieved from DynamoDB.
The script generates an HTML report with stock market analysis.
Amazon SES sends the HTML report to users via email.
CloudWatch logs the activities and monitors the system.

Setup and Deployment
(Add instructions for setting up and deploying the system, including necessary AWS configurations)
Configuration
(Add details about any configuration files or environment variables needed)
Monitoring and Logging
The system uses Amazon CloudWatch for monitoring and logging. Check the CloudWatch dashboard for:

Lambda function execution logs
EventBridge trigger status
SES email sending status
