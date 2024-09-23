# Use an official Python runtime as a parent image
FROM python:3.11.8-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (optional, not needed for this use case unless you're exposing services)
# EXPOSE 80

# Run the Python script
CMD ["python", "./stockMarketAnalysis.py"]
