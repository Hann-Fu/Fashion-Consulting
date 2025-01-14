# Use the official Python image as the base
FROM python:3.12.7-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app

# Expose the port Flask runs on
EXPOSE 5000

# Define the default command to run the Flask app
# It's recommended to use a production-ready server like Gunicorn
CMD ["flask", "run"]
