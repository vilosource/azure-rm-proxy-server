# Caching Implementation

This document describes the caching mechanism implemented in the Azure RM Proxy Server. The caching system is designed to be flexible and allows for different caching backends to be used based on the application configuration.

## Overview

The project utilizes a caching layer to reduce the number of direct calls to the Azure Resource Manager API, thereby improving performance and reducing potential API throttling. The caching system follows the **Strategy pattern**, allowing different caching implementations to be swapped in and out. A **Factory pattern** is used to create the appropriate cache instance based on the application's configuration.

## Supported Cache Types

The following cache types are supported:

- **In-Memory Cache:** Stores cached data directly in the application's memory. This is the default option and is suitable for single-instance deployments or development.
- **Redis Cache:** Uses a Redis server as the caching backend. This is suitable for distributed deployments or when a persistent cache is required.
- **No Cache:** Disables caching entirely.

## Implementation Details

The caching implementation is located in the `azure_rm_proxy/core/caching/` directory and consists of the following key components:

### `base_cache.py`

Defines the `BaseCache` abstract base class, which serves as the interface for all cache implementations. It outlines the essential methods that each cache provider must implement:

- `get(key: str) -> Optional[Any]`: Retrieves a value from the cache.
- `set(key: str, value: Any) -> None`: Stores a value in the cache without expiration.
- `set_with_ttl(key: str, value: Any, ttl: int) -> None`: Stores a value in the cache with a specified Time-To-Live (TTL) in seconds.
- `delete(key: str) -> None`: Removes a value from the cache.
- `clear() -> None`: Removes all values from the cache.

### `__init__.py`

Contains the `CacheType` enumeration, which defines the available cache types (`MEMORY`, `REDIS`, `NO_CACHE`). It also makes the cache implementations and factory available for import.

### `memory_cache.py`

Provides the `MemoryCache` class, an implementation of the `BaseCache` interface that stores cached data in a Python dictionary in memory. It includes logic to handle TTL for cached items.

### `redis_cache.py`

Provides the `RedisCache` class, an implementation of the `BaseCache` interface that uses a Redis server for caching. It connects to Redis using a provided URL and utilizes Redis commands for cache operations, including `SETEX` for TTL.

### `no_cache.py`

Provides the `NoCache` class, a no-operation implementation of the `BaseCache` interface. It fulfills the interface contract but does not perform any caching actions.

### `factory.py`

Contains the `CacheFactory` class, which is responsible for creating instances of the appropriate cache implementation based on the application's configuration. The `create_cache(settings)` static method reads the `cache_type` from the `Settings` object and returns the corresponding cache instance. It also includes fallback logic to the in-memory cache if Redis initialization fails.

## Configuration

The caching behavior is configured through environment variables, which are loaded into the `Settings` object (`azure_rm_proxy/app/config.py`):

- `CACHE_TYPE`: Specifies the cache backend to use (`memory`, `redis`, or `no_cache`). Defaults to `memory`.
- `REDIS_URL`: The connection URL for the Redis server (e.g., `redis://localhost:6379/0`). Only relevant if `CACHE_TYPE` is `redis`. Defaults to `redis://localhost:6379/0`.
- `REDIS_PREFIX`: A prefix to use for all keys stored in Redis to avoid key collisions with other applications. Defaults to `azure_rm_proxy:`.
- `CACHE_TTL`: The default Time-To-Live (TTL) for cached items in seconds. Defaults to `3600` (1 hour).

## Integration with AzureResourceService

The `AzureResourceService` (`azure_rm_proxy/core/azure_service.py`) receives an instance of a `BaseCache` implementation through dependency injection (`azure_rm_proxy/app/dependencies.py`). This allows the service and its mixins to interact with the cache using the standardized `BaseCache` interface, without needing to know the specific caching backend being used.

## Cache Invalidation

Clients can force a cache refresh for specific API calls by including the `?refresh-cache=true` query parameter in their requests. This instructs the service to bypass the cache for that particular request and fetch fresh data from Azure.

## SOLID Principles and Design Patterns in Caching

The caching implementation in this project serves as a practical example of applying SOLID principles and common design patterns. By examining the code, developers can gain a deeper understanding of these concepts and how they contribute to building maintainable, flexible, and scalable software.

### SOLID Principles

SOLID is an acronym for five design principles intended to make software designs more understandable, flexible, and maintainable.

1.  **Single Responsibility Principle (SRP):** A class should have only one reason to change. In the caching implementation:
    *   `BaseCache`: Solely defines the contract for caching operations.
    *   `MemoryCache`, `RedisCache`, `NoCache`: Each class is responsible for a single caching mechanism (in-memory, Redis, or no caching).
    *   `CacheFactory`: Its only responsibility is creating cache instances based on configuration.

    *Learning from the code:* Observe how each class in the `azure_rm_proxy/core/caching/` directory focuses on a specific task. Consider what would cause each class to change – for `MemoryCache`, it would be a change in how in-memory data is stored; for `RedisCache`, it would be a change in Redis interaction; for `CacheFactory`, it would be a change in how cache types are determined or instantiated.

2.  **Open/Closed Principle (OCP):** Software entities (classes, modules, functions, etc.) should be open for extension, but closed for modification. The caching system is open for extension because you can add new cache providers (e.g., MemcachedCache) without modifying the existing `BaseCache` interface, `CacheFactory`, or the code that uses the cache (`AzureResourceService`). It's closed for modification because adding a new cache type doesn't require changing the core logic of existing cache implementations or the service that depends on the `BaseCache` abstraction.

    *Learning from the code:* Imagine adding a new `MemcachedCache` class. You would create a new file `memcached_cache.py` implementing `BaseCache`, add a new `CacheType.MEMCACHED` to `__init__.py`, and update `CacheFactory` to handle the new type. Notice that `BaseCache`, `MemoryCache`, `RedisCache`, `NoCache`, and `AzureResourceService` remain unchanged.

3.  **Liskov Substitution Principle (LSP):** Objects of a superclass should be replaceable with objects of a subclass without affecting the correctness of the program. Since `MemoryCache`, `RedisCache`, and `NoCache` all implement the `BaseCache` interface, any of these cache instances can be used interchangeably wherever a `BaseCache` is expected (specifically in the `AzureResourceService`). The service interacts with the cache through the `BaseCache` methods (`get`, `set`, etc.) and doesn't need to know the specific underlying implementation.

    *Learning from the code:* Look at how `AzureResourceService` uses `self.cache`. It calls methods like `self.cache.get()` or `self.cache.set_with_ttl()`. The code doesn't check if `self.cache` is a `MemoryCache` or `RedisCache`; it trusts that any object implementing `BaseCache` will behave as expected. This allows you to substitute different cache implementations without breaking the service logic.

4.  **Interface Segregation Principle (ISP):** Clients should not be forced to depend on interfaces they do not use. In this caching system, the `BaseCache` interface is relatively small and focused on core caching operations. There isn't a single large interface with many methods that clients might not need. Each method in `BaseCache` is essential for a functional cache.

    *Learning from the code:* Consider if `BaseCache` included methods for, say, distributed locking or pub/sub. If a simple `MemoryCache` didn't need these features, it would be forced to implement methods it doesn't use, violating ISP. The current `BaseCache` avoids this by keeping the interface minimal and relevant to caching.

5.  **Dependency Inversion Principle (DIP):** High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions. In this project, the high-level `AzureResourceService` depends on the `BaseCache` abstraction (the interface), not on the low-level concrete implementations like `MemoryCache` or `RedisCache`. The `CacheFactory` (a lower-level detail in terms of instantiation) depends on the `BaseCache` abstraction as its return type.

    *Learning from the code:* Observe how `AzureResourceService` is initialized in `app/dependencies.py`. It receives a `cache` object of type `CacheStrategy` (which is the `BaseCache` protocol). The `AzureResourceService` code itself doesn't import `MemoryCache` or `RedisCache`. This inversion of control means the service is decoupled from the specific caching technology.

### Design Patterns

Design patterns are reusable solutions to common problems in software design. The caching implementation demonstrates the use of several patterns:

1.  **Strategy Pattern:** Defines a family of algorithms, encapsulates each algorithm, and makes the algorithms interchangeable. The Strategy pattern lets the algorithm vary independently from clients that use it. Here, the different cache implementations (`MemoryCache`, `RedisCache`, `NoCache`) represent different strategies for caching. The `BaseCache` interface defines the common interface for these strategies, and the `AzureResourceService` is the client that uses a strategy via the `BaseCache` interface.

    *Learning from the code:* See how `AzureResourceService` uses `self.cache.get()`, `self.cache.set_with_ttl()`, etc. The specific caching strategy being executed depends on the concrete type of `self.cache` at runtime, which is determined by the configuration and the `CacheFactory`.

2.  **Factory Pattern:** Provides an interface for creating families of related or dependent objects without specifying their concrete classes. The `CacheFactory` is a simple factory that encapsulates the logic for creating different types of cache instances. This decouples the client code (the dependency injection in `app/dependencies.py`) from the concrete cache class instantiation.

    *Learning from the code:* Examine the `CacheFactory.create_cache()` method. It takes configuration as input and returns a `BaseCache` object. The code that calls this method doesn't need to know the `new MemoryCache()` or `new RedisCache(...)` syntax; the factory handles that complexity.

3.  **Dependency Injection (DI):** A technique whereby one object supplies the dependencies of another object. In this project, the cache instance (a dependency of `AzureResourceService`) is injected into the `AzureResourceService` constructor by the `get_azure_service` function in `app/dependencies.py`. This is a form of constructor injection.

    *Learning from the code:* Look at the `__init__` method of `AzureResourceService` and the `get_azure_service` function. Notice how the `cache` object is created outside of `AzureResourceService` and passed in. This makes `AzureResourceService` easier to test (you can inject mock cache objects) and more flexible (you can easily change the cache implementation in one place).

By studying the caching implementation in this project, developers can see how these fundamental SOLID principles and design patterns are applied in a real-world scenario to create a well-structured and maintainable codebase.
