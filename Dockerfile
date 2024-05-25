# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements.txt file into the container
COPY requirements.txt ./

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Install python-dotenv to read environment variables from .env file
RUN pip install python-dotenv

# Copy the rest of the application code into the container
COPY . .

# Command to run the application
CMD ["python", "main.py"]
