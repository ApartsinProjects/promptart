# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.9-slim-buster as build


# Set the working directory inside the container
WORKDIR /usr/aws/projects/prompt-art-docker-events-manager

# Create the necessary directories
RUN mkdir -p /usr/aws/core /usr/aws/utils

# Copy the current directory contents into the container
COPY . .

# Copy the contents of the `utils` and `core` directories
# Make sure these paths are relative to the Docker build context
COPY utils/* /usr/aws/utils/
COPY core/* /usr/aws/core/


# install dependencies
RUN pip install -r requirements.txt

# Make sure the script is executable
RUN chmod +x run_events_manager.py

ENV PA_SQS_NAME=promptart-dev
ENV AWS_DEFAULT_REGION=us-east-1
# Run app.py when the container launches
CMD ["python", "-u", "run_events_manager.py"]