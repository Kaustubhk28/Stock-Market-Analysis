# Stock Market Analysis Report Generator

## Project Overview
This project automates the generation and distribution of daily stock market analysis reports. It fetches stock data from Alpha Vantage API, processes it using a Python script, and sends out HTML reports via email to recipients using Amazon Simple Email Service (SES).

![Project Architecture](./stockMarketAnalysisArchitectureDiagram.jpg)

## Table of Contents
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Workflow](#workflow)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Monitoring and Logging](#monitoring-and-logging)
- [Contributing](#contributing)
- [License](#license)

## Features
- Fetches stock data for multiple tickers from Alpha Vantage API
- Generates comprehensive stock analysis reports including:
  - Price and volume visualizations
  - Technical indicators (Moving Averages, RSI, Bollinger Bands)
  - Key metrics (Closing prices, volatility, gains/losses, volume trends)
  - Performance summaries
- Sends HTML reports via email using Amazon SES
- Runs daily using AWS Lambda and Amazon EventBridge
- Stores recipient email addresses in Amazon DynamoDB
- Uses Docker for consistent deployment environments

## Technologies Used
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
2. Lambda executes the Docker image of Amazon ECR containing the Python script.
3. The script performs the following actions:
   a. Fetches latest stock data from Alpha Vantage API.
   b. Retrieves subscriber email addresses from DynamoDB.
   c. Generates an HTML report with stock market analysis.
4. Amazon SES sends the HTML report to each subscriber.
5. CloudWatch logs all activities and monitors system performance.

## Setup and Installation

### Prerequisites
- AWS Account
- Docker installed on your local machine
- Python 3.8+
- Alpha Vantage API key

### Steps
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/stock-market-analysis.git
   cd stock-market-analysis
   ```

2. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up AWS CLI and configure with your credentials.

4. Create a DynamoDB table to store email addresses.

5. Set up Amazon SES and verify email addresses.

6. Create an ECR repository to store your Docker image.

7. Build and push the Docker image:
   ```
   docker build -t stock-analysis .
   docker tag stock-analysis:latest <your-ecr-repo-uri>:latest
   docker push <your-ecr-repo-uri>:latest
   ```

8. Create an AWS Lambda function using the ECR image.

9. Set up an Amazon EventBridge rule to trigger the Lambda function daily.

## Usage
Once deployed, the system will automatically:
1. Fetch stock data every morning
2. Generate analysis reports
3. Send email notifications with HTML reports to recipients

To add or modify recipients, update the DynamoDB table with the appropriate email addresses.

## Project Structure
```
stock-market-analysis/
│
├── src/
│   ├── main.py
│   ├── stock_analysis.py
│   ├── email_sender.py
│   └── utils.py
│
├── tests/
│   └── test_stock_analysis.py
│
├── Dockerfile
├── requirements.txt
├── .gitignore
├── README.md
└── config.yaml
```
## Configuration

Set the following environment variables in your Lambda function:

- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key
- `DYNAMODB_TABLE_NAME`: Name of your DynamoDB table (e.g., `subscribers`)
- `SES_SENDER_EMAIL`: Verified email address for sending reports
- `AWS_REGION`: AWS region where your services are deployed
- Update `config.yaml` with your Alpha Vantage API key and other configuration parameters.
- Modify the list of stock tickers in `src/main.py` as needed.

## Deployment
1. Ensure your Docker image is pushed to ECR.
2. Update the Lambda function to use the latest image.
3. Set appropriate environment variables in the Lambda function configuration.
4. Test the Lambda function manually before enabling the EventBridge trigger.

## Monitoring and Logging
- Use AWS CloudWatch to monitor Lambda function executions and view logs.
- Set up CloudWatch Alarms for error notifications.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


