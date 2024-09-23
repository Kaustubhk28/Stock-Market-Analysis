# Stock Market Report System

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Workflow](#workflow)
5. [Setup and Deployment](#setup-and-deployment)
6. [Configuration](#configuration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)
10. [License](#license)

## Overview

This Stock Market Report System fetches daily stock market data, generates analysis reports, and automatically emails them to subscribed users. It leverages various AWS services to ensure reliable, scalable, and automated operations.

## Architecture

![Architecture Diagram](architecture-diagram.png)

## Components

1. **Alpha Vantage API**: External API providing stock market data.
2. **Python Script**: Core logic for data fetching, processing, and report generation.
3. **Docker**: Containerization of the Python script and its dependencies.
4. **Amazon ECR (Elastic Container Registry)**: Hosts the Docker image.
5. **AWS Lambda**: Serverless compute service running the Docker image.
6. **Amazon EventBridge**: Scheduler for triggering the Lambda function.
7. **Amazon DynamoDB**: NoSQL database storing user email addresses.
8. **Amazon SES (Simple Email Service)**: Email service for sending reports.
9. **Amazon CloudWatch**: Monitoring and logging service.

## Workflow

1. Amazon EventBridge triggers the AWS Lambda function daily at 8 AM ET.
2. Lambda executes the Docker image containing the Python script.
3. The script performs the following actions:
   a. Fetches latest stock data from Alpha Vantage API.
   b. Retrieves subscriber email addresses from DynamoDB.
   c. Generates an HTML report with stock market analysis.
4. Amazon SES sends the HTML report to each subscriber.
5. CloudWatch logs all activities and monitors system performance.

## Setup and Deployment

1. **AWS Account Setup**:
   - Ensure you have an AWS account with necessary permissions.

2. **Alpha Vantage API**:
   - Sign up for an Alpha Vantage API key at https://www.alphavantage.co/

3. **Docker Image**:
   - Build the Docker image containing the Python script and dependencies.
   - Push the image to Amazon ECR:
     ```
     aws ecr get-login-password --region region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.region.amazonaws.com
     docker build -t stock-market-report .
     docker tag stock-market-report:latest your-account-id.dkr.ecr.region.amazonaws.com/stock-market-report:latest
     docker push your-account-id.dkr.ecr.region.amazonaws.com/stock-market-report:latest
     ```

4. **AWS Lambda**:
   - Create a new Lambda function, selecting "Container image" as the source.
   - Choose the ECR image you pushed in step 3.
   - Set the function timeout to an appropriate value (e.g., 5 minutes).
   - Configure environment variables (see [Configuration](#configuration) section).

5. **DynamoDB**:
   - Create a table named `subscribers` with a primary key `email`.

6. **Amazon SES**:
   - Verify your sender email address in SES.
   - If in sandbox mode, verify recipient email addresses as well.

7. **EventBridge**:
   - Create a new rule in EventBridge:
     - Schedule: Cron expression `0 13 ? * MON-FRI *` (8 AM ET, Mon-Fri)
     - Target: The Lambda function created in step 4

8. **IAM Permissions**:
   - Ensure the Lambda function's execution role has permissions for:
     - DynamoDB: Read access to the `subscribers` table
     - SES: Send email permission
     - CloudWatch: Create log groups and log events

## Configuration

Set the following environment variables in your Lambda function:

- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key
- `DYNAMODB_TABLE_NAME`: Name of your DynamoDB table (e.g., `subscribers`)
- `SES_SENDER_EMAIL`: Verified email address for sending reports
- `AWS_REGION`: AWS region where your services are deployed

## Monitoring and Logging

- **CloudWatch Logs**: 
  - Check `/aws/lambda/your-function-name` log group for Lambda execution logs.
  - Look for any errors or warnings in the logs.

- **CloudWatch Metrics**:
  - Monitor Lambda metrics like invocations, duration, and errors.
  - Set up CloudWatch Alarms for critical metrics.

- **SES Metrics**:
  - Monitor email sending success rate and bounce rate.

## Troubleshooting

1. **Lambda function times out**:
   - Increase the function timeout in Lambda configuration.
   - Optimize the Python script for faster execution.

2. **Email not received**:
   - Check SES console for sending errors.
   - Verify recipient email if in SES sandbox mode.
   - Check spam folder of recipient's email.

3. **DynamoDB read failures**:
   - Verify IAM permissions for Lambda to access DynamoDB.
   - Check DynamoDB table name in environment variables.

4. **Alpha Vantage API errors**:
   - Verify API key in environment variables.
   - Check Alpha Vantage API status and quota limits.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

