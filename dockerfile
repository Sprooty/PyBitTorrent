# Use an official Python 3.10 runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libmariadb-dev

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run your application
CMD ["python3", "/usr/src/app/example/interator.py"]
