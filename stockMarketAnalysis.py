import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd
import seaborn as sns
import boto3
import sys
import logging
import os
import math
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from botocore.exceptions import ClientError
import warnings
import numpy as np
from scipy import stats
warnings.filterwarnings("ignore")

# Set the MPLCONFIGDIR to use the /tmp directory
os.environ['MPLCONFIGDIR'] = '/tmp'

api_key = 'demo'
aws_region = 'us-east-1'
table_name = "EmailCredentials"

# Initialize a DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Boto3 SES client
ses_client = boto3.client('ses', region_name=aws_region)

def get_email_credentials():
    table = dynamodb.Table(table_name)

    try:
        # Fetch the data from DynamoDB
        response = table.scan()

        if 'Items' in response:
            # Initialize variables
            sender = None
            recipients = []  # Initialize a list for recipients

            # Loop through items and extract email addresses
            for item in response['Items']:
                if item['emailID'] == 'sender':
                    sender = item['emailAddress']
                elif item['emailID'].startswith('recipient'):  # Dynamically handle recipients
                    recipients.append(item['emailAddress'])

            # Ensure sender and recipients are valid
            if not sender:
                raise ValueError("Sender email not defined in DynamoDB")
            if not recipients:
                raise ValueError("No recipient emails found in DynamoDB")

            return sender, recipients

        else:
            raise ValueError("No email credentials found in DynamoDB")

    except ClientError as e:
        print(f"Error fetching email credentials: {e}")
        raise

# Configuration
tickers = {
    'AAPL': 'Apple Inc. - Technology company known for iPhones and Macs.',
    'MSFT': 'Microsoft Corporation - Technology company known for Windows and Office.',
    'GOOGL': 'Alphabet Inc. - Parent company of Google.',
    'AMZN': 'Amazon.com, Inc. - E-commerce and cloud computing giant.',
    'NVDA': 'NVIDIA Corporation - Technology company specializing in GPUs.',
    'TSLA': 'Tesla, Inc. - Electric vehicle and clean energy company.',
    'META': 'Meta Platforms, Inc. - Social media company formerly known as Facebook.',
    'BRK-B': 'Berkshire Hathaway Inc. - Conglomerate holding company.',
    'V': 'Visa Inc. - Financial services company specializing in payment systems.',
    'JNJ': 'Johnson & Johnson - Healthcare and pharmaceutical company.',
    'WMT': 'Walmart Inc. - Retail corporation.',
    'PG': 'Procter & Gamble Co. - Consumer goods corporation.',
    'JPM': 'JPMorgan Chase & Co. - Financial services company.',
    'MA': 'Mastercard Incorporated - Financial services company.',
    'DIS': 'The Walt Disney Company - Entertainment and media conglomerate.',
    'NFLX': 'Netflix, Inc. - Streaming service provider.',
    'PYPL': 'PayPal Holdings, Inc. - Online payments company.',
    'PFE': 'Pfizer Inc. - Pharmaceutical corporation.',
    'KO': 'The Coca-Cola Company - Beverage corporation.',
    'CSCO': 'Cisco Systems, Inc. - Networking hardware and telecommunications equipment.'
}

def get_stock_data(symbol, time_range='ytd'):
    """
    Fetch stock data for a given symbol and time range.
    
    :param symbol: Stock symbol
    :param time_range: Can be 'ytd' for year-to-date, '5y' for 5 years, or an integer for number of days
    :return: List of daily stock data
    """
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={api_key}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        time_series = data.get('Time Series (Daily)', {})
        if not time_series:
            print(f"No data found for symbol: {symbol}")
            return []

        current_date = datetime.now()
        
        if time_range == 'ytd':
            start_date = datetime(current_date.year, 1, 1)
        elif time_range == '5y':
            start_date = current_date - timedelta(days=5*365)
        elif isinstance(time_range, int):
            start_date = current_date - timedelta(days=time_range)
        else:
            raise ValueError("Invalid time_range. Use 'ytd', '5y', or an integer for days.")

        filtered_data = [
            [date_str, float(day_data['1. open']) or 0, float(day_data['2. high']) or 0,
            float(day_data['3. low']) or 0, float(day_data['4. close']) or 0,
            int(day_data['5. volume']) or 0]
            for date_str, day_data in time_series.items()
            if datetime.strptime(date_str, '%Y-%m-%d') >= start_date
        ]        
        return filtered_data
    except requests.exceptions.RequestException as e:
        print(f"Request error for symbol {symbol}: {e}")
        return []
    except ValueError as e:
        print(f"Value error processing data for symbol {symbol}: {e}")
        return []

def calculate_trend(closes):
    """Calculate the trend using linear regression."""
    closes = [0 if math.isnan(x) else x for x in closes]
    x = np.arange(len(closes))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, closes)
    trend = 'Upward' if slope > 0 else 'Downward'
    strength = abs(r_value)
    return trend, strength

def calculate_moving_averages(closes):
    """Calculate 50-day and 200-day moving averages."""
    closes = [0 if math.isnan(x) else x for x in closes]
    df = pd.Series(closes)
    ma50 = df.rolling(window=50).mean().iloc[-1] or 0
    ma200 = df.rolling(window=200).mean().iloc[-1] or 0
    return ma50, ma200

def calculate_rsi(closes, period=14):
    """Calculate Relative Strength Index."""
    closes = [0 if math.isnan(x) else x for x in closes]
    delta = pd.Series(closes).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs.iloc[-1])) if rs.iloc[-1] != np.inf else 50

def calculate_bollinger_bands(closes, period=20):
    """Calculate Bollinger Bands."""
    closes = [0 if math.isnan(x) else x for x in closes]
    df = pd.Series(closes)
    ma = df.rolling(window=period).mean().iloc[-1] or 0
    std = df.rolling(window=period).std().iloc[-1] or 0
    upper = ma + (std * 2)
    lower = ma - (std * 2)
    return upper, ma, lower

def classify_stock(df):
    """Classify stock as bullish, bearish, or stable based on price change."""
    if df.empty or 'Close' not in df.columns:
        return 'Stable'
    
    first_close = df['Close'].iloc[0]
    last_close = df['Close'].iloc[-1]
    price_change_percent = ((last_close - first_close) / first_close) * 100
    
    if price_change_percent > 5:
        return 'Bullish'
    elif price_change_percent < -5:
        return 'Bearish'
    else:
        return 'Stable'

def get_insights(data, timeframe):
    """Calculate various insights from the data based on the timeframe."""
    df = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df.sort_index(inplace=True)

    # Replace 'nan' values with 0
    df = df.fillna(0)

    first_close = df['Close'].iloc[0]
    last_close = df['Close'].iloc[-1]
    price_change = last_close - first_close
    price_change_percent = (price_change / first_close) * 100
    
    closes = df['Close'].values
    
    trend, trend_strength = calculate_trend(closes)
    ma50, ma200 = calculate_moving_averages(closes)
    rsi = calculate_rsi(closes)
    upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(closes)

    classification = classify_stock(df)

    insights = {
        'highest_close': df['Close'].max() if not math.isnan(df['Close'].max()) else 0,
        'lowest_close': df['Close'].min() if not math.isnan(df['Close'].min()) else 0,
        'average_close': df['Close'].mean() if not math.isnan(df['Close'].mean()) else 0,
        'median_close': df['Close'].median() if not math.isnan(df['Close'].median()) else 0,
        'std_dev_close': df['Close'].std() if not math.isnan(df['Close'].std()) else 0,
        'range_close': df['Close'].max() - df['Close'].min() if not math.isnan(df['Close'].max()) and not math.isnan(df['Close'].min()) else 0,
        'total_volume': df['Volume'].sum() if not math.isnan(df['Volume'].sum()) else 0,
        'median_volume': df['Volume'].median() if not math.isnan(df['Volume'].median()) else 0,
        'std_dev_volume': df['Volume'].std() if not math.isnan(df['Volume'].std()) else 0,
        'range_volume': df['Volume'].max() - df['Volume'].min() if not math.isnan(df['Volume'].max()) and not math.isnan(df['Volume'].min()) else 0,
        'max_volume_date': df['Volume'].idxmax().strftime('%Y-%m-%d'),
        'min_volume_date': df['Volume'].idxmin().strftime('%Y-%m-%d'),
        'classification': classification,
        'start_date': df.index.min().strftime('%Y-%m-%d'),
        'end_date': df.index.max().strftime('%Y-%m-%d'),
        'start_price': first_close,
        'end_price': last_close,
        'price_change': price_change,
        'price_change_percent': price_change_percent,
        'max_daily_gain': df['Close'].pct_change().max() * 100,
        'max_daily_loss': df['Close'].pct_change().min() * 100,
        'volatility': df['Close'].pct_change().std() * 100,
        'timeframe': timeframe,
        'trend': trend,
        'trend_strength': trend_strength,
        'ma50': ma50,
        'ma200': ma200,
        'rsi': rsi,
        'upper_bb': upper_bb,
        'middle_bb': middle_bb,
        'lower_bb': lower_bb
    }
    
    return insights

def plot_and_encode(data_dict):
    """Generate and encode enhanced plots to base64 for different timeframes."""
    images = {}
    for period, data in data_dict.items():
        dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in data]
        closes = [row[4] for row in data]
        volumes = [row[5] for row in data]
        
        # Replace 'nan' with 0
        closes = [0 if math.isnan(x) else x for x in closes]
        volumes = [0 if math.isnan(x) else x for x in volumes]
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15), gridspec_kw={'height_ratios': [3, 3, 3]})
        
        # Plot 1: Closing prices and volume
        ax1.set_title(f'Closing Prices and Volume - {period}')
        ax1.set_ylabel('Price ($)', color='b')
        line1 = ax1.plot(dates, closes, color='b', label='Close Price')
        ax1.tick_params(axis='y', labelcolor='b')
        
        ax1_volume = ax1.twinx()
        ax1_volume.set_ylabel('Volume', color='r')
        ax1_volume.bar(dates, volumes, alpha=0.3, color='r', label='Volume')
        ax1_volume.tick_params(axis='y', labelcolor='r')
        
        lines = line1
        lines += [plt.Rectangle((0,0),1,1,fc="r", alpha=0.3)]
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left')
        
        # Plot 2: Moving Averages
        ax2.set_title('Moving Averages')
        ax2.plot(dates, closes, color='b', label='Close Price')
        ma50 = pd.Series(closes).rolling(window=50).mean()
        ma200 = pd.Series(closes).rolling(window=200).mean()
        ax2.plot(dates, ma50, color='r', label='50-day MA')
        ax2.plot(dates, ma200, color='g', label='200-day MA')
        ax2.set_ylabel('Price ($)')
        ax2.legend(loc='upper left')
        
        # Plot 3: Bollinger Bands
        ax3.set_title('Bollinger Bands')
        ax3.plot(dates, closes, color='b', label='Close Price')
        df = pd.Series(closes)
        ma20 = df.rolling(window=20).mean()
        std20 = df.rolling(window=20).std()
        upper_bb = ma20 + (std20 * 2)
        lower_bb = ma20 - (std20 * 2)
        ax3.plot(dates, ma20, color='r', label='20-day MA')
        ax3.plot(dates, upper_bb, color='g', linestyle='--', label='Upper BB')
        ax3.plot(dates, lower_bb, color='g', linestyle='--', label='Lower BB')
        ax3.fill_between(dates, upper_bb, lower_bb, alpha=0.1, color='gray')
        ax3.set_ylabel('Price ($)')
        ax3.legend(loc='upper left')
        
        fig.autofmt_xdate()  # Rotate and align the tick labels
        fig.tight_layout()
        
        # Save the plot
        img_stream = BytesIO()
        plt.savefig(img_stream, format='png')
        plt.close()
        img_stream.seek(0)
        images[f'stock_analysis_{period}'] = base64.b64encode(img_stream.read()).decode()
    
    return images

def generate_graph_description(insights):
    def format_value(value):
        if isinstance(value, float) and math.isnan(value):
            return '0'
        elif isinstance(value, float):
            return f'{value:.2f}'
        return str(value)

    return f"""
    <h4>Graph Analysis ({insights['timeframe']}):</h4>
    <p>
    Over this {insights['timeframe']} period, the stock showed a {insights['trend'].lower()} trend 
    with a trend strength of {format_value(insights['trend_strength'])}. 
    The closing price ranged from ${format_value(insights['lowest_close'])} to ${format_value(insights['highest_close'])}, 
    with an average of ${format_value(insights['average_close'])}.
    </p>
    <p>
    The 50-day moving average is at ${format_value(insights['ma50'])}, while the 200-day moving average is at ${format_value(insights['ma200'])}. 
    {
    "The 50-day MA is above the 200-day MA, potentially indicating a bullish trend." 
    if insights['ma50'] > insights['ma200'] else 
    "The 50-day MA is below the 200-day MA, potentially indicating a bearish trend."
    }
    </p>
    <p>
    The stock's RSI is {format_value(insights['rsi'])}, suggesting it might be 
    {"overbought" if insights['rsi'] > 70 else "oversold" if insights['rsi'] < 30 else "neither overbought nor oversold"}.
    The Bollinger Bands show a width of ${format_value(insights['upper_bb'] - insights['lower_bb'])}, 
    indicating {"high" if (insights['upper_bb'] - insights['lower_bb']) > (insights['average_close'] * 0.1) else "low"} volatility.
    </p>
    <p>
    Trading volume ranged from {insights['range_volume']:,} to {insights['range_volume'] + insights['std_dev_volume']:,} shares, 
    with a median of {insights['median_volume']:,} shares. 
    The highest volume was observed on {insights['max_volume_date']}, 
    while the lowest was on {insights['min_volume_date']}.
    </p>
    <p>
    Overall, the stock can be classified as <strong>{insights['classification']}</strong> for this period, 
    with a price change of ${format_value(insights['price_change'])} ({format_value(insights['price_change_percent'])}%).
    </p>
    """

def generate_html_content(ticker, description, images, insights_dict):
    def generate_insights_html(insights):
        def format_value(value):
            if isinstance(value, float) and math.isnan(value):
                return '0'
            elif isinstance(value, float):
                return f'{value:.2f}'
            return str(value)

        return f"""
        <div class="insights-container">
            <h4>Key Insights ({insights['timeframe']}):</h4>
            <p><strong>Classification:</strong> <span class="classification {insights['classification'].lower()}">{insights['classification']}</span></p>
            <ul>
                <li><strong>Period:</strong> {insights['start_date']} to {insights['end_date']}</li>
                <li><strong>Price Change:</strong> ${format_value(insights['price_change'])} ({format_value(insights['price_change_percent'])}%)</li>
                <li><strong>Trend:</strong> {insights['trend']} (Strength: {format_value(insights['trend_strength'])})</li>
                <li><strong>50-day MA:</strong> ${format_value(insights['ma50'])}</li>
                <li><strong>200-day MA:</strong> ${format_value(insights['ma200'])}</li>
                <li><strong>RSI:</strong> {format_value(insights['rsi'])}</li>
                <li><strong>Bollinger Bands:</strong> Upper: ${format_value(insights['upper_bb'])}, Middle: ${format_value(insights['middle_bb'])}, Lower: ${format_value(insights['lower_bb'])}</li>
                <li><strong>Highest Close:</strong> ${format_value(insights['highest_close'])}</li>
                <li><strong>Lowest Close:</strong> ${format_value(insights['lowest_close'])}</li>
                <li><strong>Average Close:</strong> ${format_value(insights['average_close'])}</li>
                <li><strong>Volatility:</strong> {format_value(insights['volatility'])}%</li>
                <li><strong>Max Daily Gain:</strong> {format_value(insights['max_daily_gain'])}%</li>
                <li><strong>Max Daily Loss:</strong> {format_value(insights['max_daily_loss'])}%</li>
                <li><strong>Total Volume:</strong> {insights['total_volume']:,} shares</li>
                <li><strong>Highest Volume Day:</strong> {insights['max_volume_date']}</li>
                <li><strong>Lowest Volume Day:</strong> {insights['min_volume_date']}</li>
            </ul>
        </div>
        """
    graph_template = """
    <div class="graph-container">
        <h4>{title}</h4>
        <img src="data:image/png;base64,{img_src}" alt="{alt_text}">
        {insights}
        {description}
    </div>
    """

    graph_sections = ''.join([
        graph_template.format(
            title=f"Stock Analysis - {timeframe}",
            img_src=images[f'stock_analysis_{key}'],
            alt_text=f"Stock Analysis - {timeframe}",
            insights=generate_insights_html(insights),
            description=generate_graph_description(insights)
        )
        for key, (timeframe, insights) in insights_dict.items()
    ])

    return f"""
    <section class="stock-section">
        <h2>{ticker}</h2>
        <p class="stock-description">{description}</p>
        <h3>Graphs and Insights:</h3>
        <div class="graphs-container">
            {graph_sections}
        </div>
        <p class="summary">
            The performance of {ticker} varies across different timeframes. Please refer to the detailed insights and descriptions above for each specific period. Consider the trend, moving averages, RSI, Bollinger Bands, and volume patterns when making investment decisions.
        </p>
    </section>
    """
    
def format_table_as_html(df):
    """Format the pandas DataFrame as an HTML table with equal column width, center-aligned values, and proper borders."""
    return df.style.set_table_styles(
        [
            {'selector': 'th', 'props': [('font-size', '12pt'), ('background-color', '#2C3E50'), ('color', 'white'), ('text-align', 'center'), ('border', '1px solid #ddd'), ('width', '100px')]},
            {'selector': 'td', 'props': [('padding', '8px'), ('text-align', 'center'), ('border', '1px solid #ddd'), ('width', '100px')]},
            {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f2f2f2')]},
            {'selector': 'tr:nth-child(odd)', 'props': [('background-color', '#ffffff')]},
        ]
    ).set_properties(**{
        'text-align': 'center',
        'border-collapse': 'collapse',
        'border': '1px solid #ddd',
        'width': '100px',  # Set equal column width
        'padding': '8px'
    }).hide(axis='index').to_html()  # hide the index column

html_start = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Market Analysis Report</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            background-color: #f5f5f5;
        }
        header { 
            background: linear-gradient(to right, #2C3E50, #4CA1AF); 
            color: white; 
            padding: 20px; 
            text-align: center; 
            border-radius: 10px 10px 0 0;
        }
        footer { 
            background: #2C3E50; 
            color: white; 
            padding: 10px; 
            text-align: center; 
            margin-top: 20px;
            border-radius: 0 0 10px 10px;
        }
        h1 { margin: 0; font-size: 2.5em; }
        h2 { color: #2C3E50; border-bottom: 2px solid #4CA1AF; padding-bottom: 10px; }
        h3 { color: #4CA1AF; }
        h4 { color: #2C3E50; }
        section { 
            background: white; 
            margin-bottom: 20px; 
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .stock-section { margin-bottom: 40px; }
        .stock-description { font-style: italic; color: #666; }
        .graphs-container { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 20px; 
            justify-content: space-between; 
        }
        .graph-container { 
            flex: 1 1 45%; 
            min-width: 300px;
            background: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 0 5px rgba(0,0,0,0.05);
        }
        .graph-container img { 
            width: 100%; 
            height: auto;
            border-radius: 5px;
        }
        .insights-container {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        .insights-container ul {
            list-style-type: none;
            padding-left: 0;
        }
        .insights-container li {
            margin-bottom: 5px;
        }
        .classification {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-weight: bold;
        }
        .bullish { background-color: #4CAF50; color: white; }
        .bearish { background-color: #F44336; color: white; }
        .stable { background-color: #FFC107; color: black; }
        .summary { 
            font-size: 1.1em; 
            background-color: #e9ecef; 
            padding: 15px; 
            border-radius: 8px;
            margin-top: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #4CA1AF;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
    </style>
</head>
<body>
<header>
    <h1>Daily Stock Market Analysis Report</h1>
</header>
"""
html_end = """
<footer>
    <p>&copy; 2024 Stock Market Analysis Report | Powered by Alpha Vantage API</p>
</footer>
</body>
</html>
"""

def send_email_with_attachment(html_content, filename="stock_report.html"):
    """Send the generated HTML content as an email attachment via SES."""
    
    # Fetch email addresses from DynamoDB
    sender_email, recipient_email = get_email_credentials()

    # Create the MIME email object
    msg = MIMEMultipart()
    msg['Subject'] = 'Daily Stock Market Analysis Report'
    msg['From'] = sender_email
    msg['To'] = ', '.join(recipient_email)  # Join recipient list into a single string

    # Add email body
    body = """
    Dear User,
    
    Today's Daily Stock Market Analysis Report is now available, offering insights on key stocks across 7-day, 30-day, 6-month, 1-year, YTD, and 5-year timeframes.
    
    Report Highlights:

    - Stock Classification (Bullish, Bearish, Stable)
    - Price and Volume Visualizations
    - Technical Indicators (Moving Averages, RSI, Bollinger Bands)
    - Key Metrics (Closing prices, volatility, gains/losses, volume trends)
    - Performance Summaries

    Please review the attached HTML file for the full, interactive report. 
    
    Best regards,
    Kaustubh Sunil Khedekar
    """

    msg.attach(MIMEText(body, 'plain'))

    # Attach the HTML content as a file
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(html_content.encode('utf-8'))
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={filename}')
    msg.attach(part)

    # Send the email via AWS SES
    try:
        response = ses_client.send_raw_email(
            Source=sender_email,
            Destinations=recipient_email,  # Wrap the single email in a list
            RawMessage={'Data': msg.as_string()}
        )
        print(f"Email with attachment sent successfully: {response}")
    except Exception as e:
        print(f"Error sending email: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

LOCK_FILE_PATH = '/tmp/stock_report.lock'

def lambda_handler(event, context):
    """Main Lambda function handler."""
    
    # Check if context is a dict (for local testing) or has the expected attributes
    if isinstance(context, dict):
        logger.info("Running in local/test environment")
        function_name = "local_test"
        function_version = "test"
        remaining_time = "N/A"
    else:
        function_name = getattr(context, 'function_name', 'unknown')
        function_version = getattr(context, 'function_version', 'unknown')
        remaining_time = getattr(context, 'get_remaining_time_in_millis', lambda: 'unknown')()

    logger.info(f"Function name: {function_name}")
    logger.info(f"Function version: {function_version}")
    logger.info(f"Remaining time: {remaining_time}")

    # Check if the lock file exists, indicating that the report has already been generated.
    if os.path.exists(LOCK_FILE_PATH):
        logger.info("Process has already run. Exiting.")
        return {
            'statusCode': 200,
            'body': 'Stock Market Report already generated and sent!'
        }
    
    # Use event to potentially customize the report
    custom_tickers = event.get('tickers', tickers)
    
    html_content = ""
    for ticker, description in custom_tickers.items():
        try:
            # Fetch data for different timeframes
            data_dict = {
                '7_days': get_stock_data(ticker, 7),
                '30_days': get_stock_data(ticker, 30),
                '6_months': get_stock_data(ticker, 180),
                '1_year': get_stock_data(ticker, 365),
                'ytd': get_stock_data(ticker, 'ytd'),
                '5_years': get_stock_data(ticker, '5y')
            }

            if data_dict['30_days']:
                # Calculate insights for each timeframe
                insights_dict = {
                    key: (timeframe, get_insights(data, timeframe))
                    for key, (timeframe, data) in [
                        ('7_days', ('7 Days', data_dict['7_days'])),
                        ('30_days', ('30 Days', data_dict['30_days'])),
                        ('6_months', ('6 Months', data_dict['6_months'])),
                        ('1_year', ('1 Year', data_dict['1_year'])),
                        ('ytd', ('Year-to-Date', data_dict['ytd'])),
                        ('5_years', ('5 Years', data_dict['5_years']))
                    ]
                }

                # Plot graphs and encode as base64
                images = plot_and_encode(data_dict)

                # Generate the HTML content for this stock
                stock_html = generate_html_content(ticker, description, images, insights_dict)

                # Append this stock's report to the full HTML content
                html_content += stock_html
            else:
                logger.warning(f"No data available for {ticker}. Skipping this stock.")
        except Exception as e:
            logger.error(f"Error processing data for {ticker}: {str(e)}")
            continue

    # Finalize the complete HTML content
    complete_html = html_start + html_content + html_end

    try:
        # Send the HTML content as an email attachment
        send_email_with_attachment(complete_html)
        logger.info("Email with attachment sent successfully.")

        # Create the lock file to indicate the process has been completed
        open(LOCK_FILE_PATH, 'w').close()

        return {
            'statusCode': 200,
            'body': 'Stock Market Report Generated and Email Sent Successfully!'
        }
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Failed to send Stock Market Report: {str(e)}'
        }

# For local testing
if __name__ == "__main__":
    response = lambda_handler({}, {})
    print(response)
    # Ensure exit after generating statusCode 200
    sys.exit(0)
