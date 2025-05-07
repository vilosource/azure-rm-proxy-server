#!/usr/bin/env python
"""
Test script to verify Redis caching functionality.
"""

import asyncio
import json
import time
import argparse
import os
import sys
from datetime import datetime
import pytest  # Add pytest import

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from azure_rm_proxy.core.caching import CacheType
from azure_rm_proxy.core.caching.redis_cache import RedisCache


@pytest.mark.asyncio  # Add this marker to tell pytest this is an async test
async def test_redis_caching():
    """Test basic Redis caching functionality."""
    print("Testing Redis caching functionality...")

    # Redis connection parameters
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_prefix = os.getenv("REDIS_PREFIX", "test_redis_cache:")

    print(f"Connecting to Redis at {redis_url} with prefix '{redis_prefix}'")

    try:
        # Create Redis cache instance
        redis_cache = RedisCache(redis_url=redis_url, prefix=redis_prefix)

        # Test basic operations
        test_key = "test_key"
        test_value = {
            "id": "test_id",
            "name": "test_name",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "field1": "value1",
                "field2": 123,
                "field3": [1, 2, 3],
                "field4": {"nested": "value"},
            },
        }

        # Set a value
        print(f"Setting value for key '{test_key}'...")
        redis_cache.set(test_key, test_value)

        # Get the value
        print(f"Getting value for key '{test_key}'...")
        retrieved_value = redis_cache.get(test_key)

        if retrieved_value == test_value:
            print("✅ Basic get/set test passed!")
        else:
            print("❌ Basic get/set test failed!")
            print(f"Original: {test_value}")
            print(f"Retrieved: {retrieved_value}")

        # Test TTL functionality
        ttl_key = "ttl_test_key"
        ttl_seconds = 2

        print(f"Setting value for key '{ttl_key}' with TTL of {ttl_seconds} seconds...")
        redis_cache.set_with_ttl(ttl_key, test_value, ttl_seconds)

        # Verify it exists
        ttl_value = redis_cache.get(ttl_key)
        if ttl_value:
            print("✅ Value with TTL was stored successfully!")
        else:
            print("❌ Value with TTL was not stored!")

        # Wait for TTL to expire
        print(f"Waiting {ttl_seconds + 1} seconds for TTL to expire...")
        await asyncio.sleep(ttl_seconds + 1)

        # Try to get the value after TTL expiration
        expired_value = redis_cache.get(ttl_key)
        if expired_value is None:
            print("✅ TTL expiration test passed!")
        else:
            print("❌ TTL expiration test failed! Value still exists after TTL period.")

        # Test delete functionality
        print(f"Deleting key '{test_key}'...")
        redis_cache.delete(test_key)

        # Verify it was deleted
        deleted_value = redis_cache.get(test_key)
        if deleted_value is None:
            print("✅ Delete test passed!")
        else:
            print("❌ Delete test failed! Value still exists after deletion.")

        # Test clear functionality with prefix
        clear_prefix = "clear_test:"
        clear_cache = RedisCache(redis_url=redis_url, prefix=clear_prefix)

        # Set multiple values with the clear prefix
        for i in range(5):
            clear_cache.set(f"key_{i}", f"value_{i}")

        print(f"Clearing all keys with prefix '{clear_prefix}'...")
        clear_cache.clear()

        # Verify they were all cleared
        all_cleared = True
        for i in range(5):
            if clear_cache.get(f"key_{i}") is not None:
                all_cleared = False
                break

        if all_cleared:
            print("✅ Clear test passed!")
        else:
            print("❌ Clear test failed! Some values still exist after clearing.")

        print("\nAll Redis cache tests completed!")

    except Exception as e:
        print(f"Error testing Redis cache: {e}")
        return False

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Redis caching functionality")
    parser.add_argument("--redis-url", dest="redis_url", help="Redis connection URL")
    parser.add_argument("--redis-prefix", dest="redis_prefix", help="Redis key prefix")

    args = parser.parse_args()

    # Override environment variables with command-line arguments
    if args.redis_url:
        os.environ["REDIS_URL"] = args.redis_url
    if args.redis_prefix:
        os.environ["REDIS_PREFIX"] = args.redis_prefix

    # Run the test
    success = asyncio.run(test_redis_caching())

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
