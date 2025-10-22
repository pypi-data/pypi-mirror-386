# PgConnect

PgConnect is a PostgreSQL connection and ORM library for Python. It provides an easy-to-use interface for connecting to PostgreSQL databases and performing common database operations.

## Features

- Easy connection to PostgreSQL databases
- ORM-like interface for defining and interacting with database tables
- Support for various PostgreSQL data types
- **Advanced caching mechanism** with Redis support for improved performance
- **RecordLike objects** that behave exactly like `asyncpg.Record` for cached data
- Connection pooling for high-performance applications
- Comprehensive filtering and search capabilities

## Installation

You can install PgConnect using pip:

```bash
pip install pgconnect
```

## Requirements

- Python 3.6+
- asyncpg
- cachetools
- redis (for Redis caching support)

## Caching

PgConnect supports **two types of caching** to improve performance by reducing database queries:

1. **In-Memory Caching** (TTLCache): Fast, local caching using Python's memory
2. **Redis Caching**: Distributed caching with Redis for scalable applications

### **Caching Types**

#### **In-Memory Caching**

```python
users = pgconnect.Table(
    name="users",
    connection=connection,
    columns=columns,
    cache=True,              # Enable in-memory caching
    cache_key="id",          # Cache key for lookups
    cache_ttl=300,           # TTL in seconds (5 minutes)
    cache_maxsize=1000       # Maximum cache entries
)
```

#### **Redis Caching**

```python
# Set up Redis connection
redis_connection = pgconnect.RedisConnection(
    host='localhost',
    port=6379,
    password='your_password',
    decode_responses=True
)

users = pgconnect.Table(
    name="users",
    connection=connection,
    columns=columns,
    redis_cache=True,              # Enable Redis caching
    redis_connection=redis_connection,
    cache_key="id",                # Cache key for lookups
    cache_ttl=300                  # TTL in seconds (5 minutes)
)
```

### **RecordLike Objects**

Cached database records are returned as **RecordLike objects** that behave exactly like `asyncpg.Record`:

```python
# Insert and cache a user
user = await users.insert(name="John", email="john@example.com")

# Get from cache - returns RecordLike object
cached_user = await users.getCache("user_1")

# Access data like asyncpg.Record
print(cached_user.name)           # Attribute access
print(cached_user['email'])       # Dictionary access
print(cached_user.get('age', 0))  # get() method with default
print(len(cached_user))           # Length
print('name' in cached_user)      # Membership test

# Iterate over values
for value in cached_user:
    print(value)

# Get keys, values, items
for key in cached_user.keys():
    print(key)
```

### **Benefits of Caching**

1. **Reduced Latency:** Queries served directly from cache (microseconds vs milliseconds)
2. **Lower Database Load:** Fewer queries sent to PostgreSQL server
3. **Improved Scalability:** Handle more concurrent requests efficiently
4. **Distributed Caching:** Redis support for multi-instance applications
5. **Record Compatibility:** Cached objects behave exactly like original `asyncpg.Record` objects

### **When to Use Caching**

- **In-Memory Caching**: Single-instance applications, fast local access
- **Redis Caching**: Multi-instance applications, shared cache across services
- For frequently read data that doesn't change often
- To optimize expensive database queries and improve response times

### **Advanced Caching Example**

Here’s an example showing how caching can improve performance:

```python
# Enable caching for the table with a cache key
users = pgconnect.Table(
    name="users",
    connection=connection,
    columns=[
        pgconnect.Column(name="id", type=pgconnect.DataType.SERIAL().primary_key().not_null()),
        pgconnect.Column(name="email", type=pgconnect.DataType.VARCHAR().unique().not_null()),
        pgconnect.Column(name="username", type=pgconnect.DataType.VARCHAR()),
        pgconnect.Column(name="password", type=pgconnect.DataType.TEXT()),
        pgconnect.Column(name="created_at", type=pgconnect.DataType.TIMESTAMP().default("NOW()")),
    ],
    cache=True,  # Enable caching
    cache_key="id",  # Specify cache key for lookups
    cache_ttl=60  # Cache TTL in seconds (optional, default is no expiry)
    cache_maxsize=1000  # Maximum number of items in the cache (optional, default is 1000)
)

# First query - data fetched from the database and stored in cache
user = await users.select("id", "username", email="example@gmail.com")
print("Fetched from database:", user)

# Subsequent query with the same parameters - data fetched from cache
cached_user = await users.select("id", "username", email="example@gmail.com")
print("Fetched from cache:", cached_user)
```

Performance Comparison:

- Without Caching: Each query triggers a request to the PostgreSQL server, which involves network overhead and database processing time.
- With Caching: After the first query, subsequent requests with the same parameters are served from the cache, reducing query time from milliseconds to microseconds.

**Performance Comparison:**

- **Without Caching:** Each query = PostgreSQL network request (5-50ms)
- **With In-Memory Caching:** Cached queries served in microseconds
- **With Redis Caching:** Distributed cache across multiple instances

By using caching strategically in your application, you can significantly improve response times and reduce database workload.

## Usage

### Connecting to the Database

```python
import pgconnect
import asyncio

async def main():
    connection = pgconnect.Connection(
        host="your_host",
        port=5432,
        user="your_user",
        password="your_password",
        database="your_database"
    )

    # Define your table schema
    users = pgconnect.Table(
        name="users",
        connection=connection,
        columns=[
            pgconnect.Column(
                name="id",
                type=pgconnect.DataType.SERIAL().primary_key().not_null()
            ),
            pgconnect.Column(
                name="email",
                type=pgconnect.DataType.VARCHAR().unique().not_null()
            ),
            pgconnect.Column(
                name="username",
                type=pgconnect.DataType.VARCHAR()
            ),
            pgconnect.Column(
                name="password",
                type=pgconnect.DataType.TEXT(),
            ),
            pgconnect.Column(
                name="created_at",
                type=pgconnect.DataType.TIMESTAMP().default("NOW()")
            )
        ],
        cache=True,         # Enable in-memory caching
        cache_key="id"      # Cache by ID field
    )

    await users.create()
    print(users)

if __name__ == "__main__":
    asyncio.run(main())
```

**Note:** The above example uses in-memory caching. For Redis caching, replace `cache=True` with `redis_cache=True` and add a `redis_connection` parameter.

### Inserting Data

```python
await users.insert(
    email="example@gmail.com",
    username="example",
    password="password"
)
```

Here, this is inserting a new row into the `users` table with the `email` as `example@gmail.com`, `username` as `example`, and `password` as `password`.

### Selecting Data

```python
user = await users.select("id", "username", email="example@gmail.com")
print(user)
```

Here, this is selecting the `id` and `username` columns for the row where the `email` is `example@gmail.com`.

### Updating Data

```python
await users.update({"id": 1}, username="new_username")
```

Here, this is updating the `username` column to `new_username` for the row where the `id` is `1`.

### Deleting Data

```python
await users.delete(id=1)
```

Here, this is deleting the row from the `users` table where the `id` is `1`.

### Cache Operations

```python
# Set cache value
await users.setCache("user_123", user_data)

# Get cache value (returns RecordLike object for records)
cached_user = await users.getCache("user_123")

# Check if cache key exists
exists = await users.cacheExists("user_123")

# Clear Redis cache for table
await users.clear_redis_cache()

# Ping Redis connection
ping_time = await users.pingRedis()
print(f"Redis ping: {ping_time}ms")
```

### Counting Rows

```python
user_count = await users.count()
print(user_count)
```

Here, this is counting the total number of rows in the `users` table.

### Checking Existence

```python
user_exists = await users.exists(id=1)
print(user_exists)
```

Here, this is checking if there is any row in the `users` table where the `id` is `1`.

### Getting Columns

```python
columns = await users.get_columns()
print(columns)
```

Here, this is retrieving the names and data types of all columns in the `users` table.

### Dropping the Table

```python
await users.drop()
```

Here, this is dropping the `users` table from the PostgreSQL database.

### Truncating the Table

```python
await users.truncate()
```

Here, this is truncating the `users` table, which removes all rows from the table.

### Example Usage in a Script

Here is a complete example script demonstrating how to use these methods:

```python
import pgconnect
import asyncio

async def main():
    connection = pgconnect.Connection(
        host="your_host",
        port=5432,
        user="your_user",
        password="your_password",
        database="your_database"
    )

    users = pgconnect.Table(
        name="users",
        connection=connection,
        columns=[
            pgconnect.Column(
                name="id",
                type=pgconnect.DataType.SERIAL().primary_key().not_null()
            ),
            pgconnect.Column(
                name="email",
                type=pgconnect.DataType.VARCHAR().unique().not_null()
            ),
            pgconnect.Column(
                name="username",
                type=pgconnect.DataType.VARCHAR()
            ),
            pgconnect.Column(
                name="password",
                type=pgconnect.DataType.TEXT(),
            ),
            pgconnect.Column(
                name="created_at",
                type=pgconnect.DataType.TIMESTAMP().default("NOW()")
            )
        ],
        cache=True,
        cache_key="id",
    )

    await users.create()
    print("Table created")

    # Insert data
    await users.insert(
        email="example@gmail.com",
        username="example",
        password="password"
    )
    print("Data inserted")

    # Select data
    user = await users.select("id", "username", email="example@gmail.com")
    print("Selected user:", user)

    # Update data
    await users.update({"id": 1}, username="new_username")
    print("Data updated")

    # Delete data
    await users.delete(id=1)
    print("Data deleted")

    # Count rows
    user_count = await users.count()
    print("User count:", user_count)

    # Check existence
    user_exists = await users.exists(id=1)
    print("User exists:", user_exists)

    # Get columns
    columns = await users.get_columns()
    print("Table columns:", columns)

    # Drop table
    await users.drop()
    print("Table dropped")

    # Truncate table
    await users.truncate()
    print("Table truncated")

if __name__ == "__main__":
    asyncio.run(main())
```

This script demonstrates how to use the `Table` class to perform various database operations, including creating a table, inserting, updating, deleting, selecting data, counting rows, checking existence, getting columns, dropping the table, and truncating the table.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

AdnanBinPulok - [GitHub](https://github.com/AdnanBinPulok)
