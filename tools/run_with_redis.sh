#!/bin/bash
# Script to start the Azure RM Proxy Server with Redis caching

# Check if Redis is already running
echo "Checking if Redis is already running..."
if docker ps | grep -q azure-rm-proxy-server-redis; then
    echo "Redis is already running."
else
    # Start Redis using docker compose
    echo "Starting Redis container..."
    docker compose up -d redis
    
    # Wait for Redis to be healthy
    echo "Waiting for Redis to be ready..."
    attempt=1
    max_attempts=10
    while [ $attempt -le $max_attempts ]; do
        if docker compose exec redis redis-cli ping | grep -q 'PONG'; then
            echo "Redis is ready!"
            break
        fi
        echo "Waiting for Redis to be ready (attempt $attempt/$max_attempts)..."
        sleep 2
        attempt=$((attempt + 1))
        
        if [ $attempt -gt $max_attempts ]; then
            echo "Redis failed to start properly after $max_attempts attempts."
            echo "Please check the Redis container logs: docker compose logs redis"
            exit 1
        fi
    done
fi

# Set environment variables for Redis caching
export CACHE_TYPE=redis
export REDIS_URL=redis://localhost:6379/0
export REDIS_PREFIX="azure_rm_proxy:"

# Start the Azure RM Proxy Server
echo "Starting Azure RM Proxy Server with Redis caching..."
echo "Cache settings:"
echo "  CACHE_TYPE: $CACHE_TYPE"
echo "  REDIS_URL: $REDIS_URL"
echo "  REDIS_PREFIX: $REDIS_PREFIX"
echo ""

# Run the server using the poetry script entry point
poetry run start-proxy