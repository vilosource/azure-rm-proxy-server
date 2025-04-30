# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir poetry && \
    poetry install --no-root --no-dev

# Expose the port the app runs on
EXPOSE 7890 

# Set environment variables for Redis caching
ENV CACHE_TYPE=redis \
    REDIS_URL=redis://localhost:6379/0 \
    REDIS_PREFIX=azure_rm_proxy:

# Command to run the application
CMD ["poetry", "run", "start-proxy"]