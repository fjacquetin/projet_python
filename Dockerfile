# Use Python as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install Linux packages
RUN apt-get update && apt-get install -y curl git vim && apt-get clean

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Set the command to run the application
CMD ["python", "main.py"]