FastAPI ORM - Complete Features Guide

📚 Table of Contents

1. Overview
2. Field Types
3. Advanced Querying
4. Pagination
5. Bulk Operations
6. Soft Delete
7. Transactions
8. Field Validators
9. Exception Handling
10. Auto Timestamps
11. Database Health Checks & Monitoring
12. Query Result Caching
13. Database Seeding
14. Composite Constraints
15. Raw SQL Support
16. Query Performance Monitoring
17. Complete FastAPI Examples
18. Migration Guide
19. Performance Improvements

Overview

FastAPI ORM is a powerful, production-ready ORM library designed specifically for FastAPI applications. Version 0.3.0 introduces comprehensive features while maintaining full backward compatibility with v0.2.0.

Field Types

Basic Field Types

```python
from fastapi_orm import Model, IntegerField, StringField, BooleanField, TextField, DateTimeField

class User(Model):
    __tablename__ = "users"
    
    id: int = IntegerField(primary_key=True)
    username: str = StringField(max_length=50, min_length=3, nullable=False)
    email: str = StringField(max_length=255, nullable=False, unique=True)
    is_active: bool = BooleanField(default=True)
    bio: str = TextField(nullable=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

DecimalField

Precise decimal numbers for financial and scientific data.

```python
from fastapi_orm import Model, IntegerField, StringField, DecimalField
from decimal import Decimal

class Product(Model):
    __tablename__ = "products"
    
    id: int = IntegerField(primary_key=True)
    name: str = StringField(max_length=100)
    price: Decimal = DecimalField(precision=10, scale=2, nullable=False)
    discount: Decimal = DecimalField(precision=5, scale=2, default=Decimal("0.00"))
```

UUIDField

UUID primary keys and identifiers with auto-generation support.

```python
from fastapi_orm import Model, StringField, UUIDField
import uuid

class User(Model):
    __tablename__ = "users"
    
    id: uuid.UUID = UUIDField(primary_key=True, auto_generate=True)
    external_id: uuid.UUID = UUIDField(unique=True, auto_generate=True)
    username: str = StringField(max_length=50)
```

EnumField

Type-safe enumerated values.

```python
from fastapi_orm import Model, IntegerField, StringField, EnumField
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class User(Model):
    __tablename__ = "users"
    
    id: int = IntegerField(primary_key=True)
    username: str = StringField(max_length=50)
    role: UserRole = EnumField(UserRole, nullable=False, default=UserRole.USER)
```

Advanced Querying

Filter with Operators

Use dictionary-based operators for complex filtering:

```python
# Comparison operators
users = await User.filter_by(session, age={"gt": 25})
users = await User.filter_by(session, age={"gte": 18})
users = await User.filter_by(session, age={"lt": 65})
users = await User.filter_by(session, age={"lte": 30})
users = await User.filter_by(session, status={"ne": "banned"})

# List operators
users = await User.filter_by(session, role={"in": ["admin", "moderator"]})
users = await User.filter_by(session, role={"not_in": ["guest"]})

# String operators
users = await User.filter_by(session, username={"contains": "john"})
users = await User.filter_by(session, email={"icontains": "gmail"})
users = await User.filter_by(session, username={"startswith": "admin_"})
users = await User.filter_by(session, email={"endswith": "@company.com"})
```

Ordering and Sorting

```python
# Order by single field
users = await User.filter_by(session, order_by="created_at")
users = await User.filter_by(session, order_by="-created_at")  # descending

# Multiple order fields
users = await User.filter_by(session, order_by=["is_active", "-created_at"])

# Combine with filters and limits
active_users = await User.filter_by(
    session,
    is_active=True,
    order_by="-created_at",
    limit=10
)
```

Count and Exists

```python
# Count operations
total_users = await User.count(session)
active_count = await User.count(session, is_active=True)

# Existence checks
exists = await User.exists(session, username="john_doe")
exists = await User.exists(session, username="john", is_active=True)
```

Get or Create

```python
# Get existing or create new record
user, created = await User.get_or_create(
    session,
    username="john_doe",
    defaults={"email": "john@example.com", "age": 25}
)

if created:
    print("New user created!")
else:
    print("User already existed!")
```

Pagination

Simple Pagination

```python
# Basic pagination
result = await User.paginate(session, page=1, page_size=20)

print(f"Total: {result['total']}")
print(f"Page: {result['page']} of {result['total_pages']}")
print(f"Items: {len(result['items'])}")
print(f"Has next: {result['has_next']}")
print(f"Has previous: {result['has_prev']}")

for user in result['items']:
    print(user.username)
```

Advanced Pagination

```python
# Paginate with filters and ordering
result = await User.paginate(
    session,
    page=2,
    page_size=10,
    order_by="-created_at",
    is_active=True,
    age={"gte": 18}
)
```

Bulk Operations

Bulk Create

```python
# Create multiple records at once
users_data = [
    {"username": "user1", "email": "user1@example.com", "age": 25},
    {"username": "user2", "email": "user2@example.com", "age": 30},
    {"username": "user3", "email": "user3@example.com", "age": 35},
]

users = await User.bulk_create(session, users_data)
print(f"Created {len(users)} users")
```

Bulk Update

```python
# Update multiple records
updates = [
    {"id": 1, "age": 26, "is_active": True},
    {"id": 2, "age": 31, "is_active": False},
    {"id": 3, "age": 36, "is_active": True},
]

updated_count = await User.bulk_update(session, updates)
print(f"Updated {updated_count} users")
```

Bulk Delete

```python
# Delete multiple records by IDs
deleted_count = await User.bulk_delete(session, [1, 2, 3, 4, 5])
print(f"Deleted {deleted_count} users")
```

Soft Delete

Using SoftDeleteMixin

```python
from fastapi_orm import Model, SoftDeleteMixin, IntegerField, StringField, TextField

class Post(Model, SoftDeleteMixin):
    __tablename__ = "posts"
    
    id: int = IntegerField(primary_key=True)
    title: str = StringField(max_length=200, nullable=False)
    content: str = TextField(nullable=False)
```

Soft Delete Operations

```python
# Create and soft delete
post = await Post.create(session, title="My Post", content="Content")
await post.soft_delete(session)
print(post.is_deleted)  # True

# Restore soft-deleted record
await post.restore(session)
print(post.is_deleted)  # False

# Query operations
deleted_posts = await Post.only_deleted(session)
all_posts = await Post.all_with_deleted(session)
active_posts = await Post.all(session)  # Only non-deleted by default
```

Transactions

Transaction Decorator

```python
from fastapi_orm import transactional

@transactional
async def create_user_with_posts(session: AsyncSession, username: str, email: str):
    # Everything in this function runs in a transaction
    user = await User.create(session, username=username, email=email)
    
    for i in range(3):
        await Post.create(
            session,
            title=f"Post {i}",
            content=f"Content {i}",
            author_id=user.id
        )
    
    return user
    # Auto-commits on success, auto-rolls back on exception
```

Transaction Context Manager

```python
from fastapi_orm import transaction

async with db.session() as session:
    async with transaction(session):
        user = await User.create(session, username="john", email="john@example.com")
        post = await Post.create(session, title="Post", content="Content", author_id=user.id)
        # Auto-commits here, or rolls back on exception
```

Atomic Function

```python
from fastapi_orm import atomic

async def create_user_and_post(session, username, email, title, content):
    user = await User.create(session, username=username, email=email)
    post = await Post.create(session, title=title, content=content, author_id=user.id)
    return user, post

async with db.session() as session:
    user, post = await atomic(session, create_user_and_post, "john", "john@example.com", "Title", "Content")
```

Field Validators

Built-in Validators

```python
from fastapi_orm import Model, IntegerField, StringField

class User(Model):
    __tablename__ = "users"
    
    id: int = IntegerField(primary_key=True)
    
    # Min/max value constraints
    age: int = IntegerField(min_value=0, max_value=150, nullable=False)
    
    # Min/max length for strings
    username: str = StringField(
        max_length=50,
        min_length=3,
        nullable=False
    )
    
    # Email with custom validator
    email: str = StringField(
        max_length=255,
        validators=[lambda x: "@" in x and "." in x],
        nullable=False
    )
```

Custom Validators

```python
def validate_username(value: str) -> bool:
    # Only alphanumeric and underscores
    return value.replace("_", "").isalnum()

def validate_age(value: int) -> bool:
    return 13 <= value <= 120

class User(Model):
    __tablename__ = "users"
    
    id: int = IntegerField(primary_key=True)
    username: str = StringField(
        max_length=50,
        validators=[validate_username],
        nullable=False
    )
    age: int = IntegerField(
        validators=[validate_age],
        nullable=False
    )
```

Validation Errors

```python
from fastapi_orm.exceptions import ValidationError

try:
    user = await User.create(session, username="a", age=200)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Field: {e.details['field']}")
```

Exception Handling

Custom Exceptions

```python
from fastapi_orm.exceptions import (
    FastAPIOrmException,
    RecordNotFoundError,
    DuplicateRecordError,
    ValidationError,
    DatabaseError,
    TransactionError,
)

try:
    user = await User.get(session, 999)
    if not user:
        raise RecordNotFoundError("User", id=999)
except RecordNotFoundError as e:
    print(e.message)  # "User not found with id=999"
    print(e.details)  # {"model": "User", "filters": {"id": 999}}
```

FastAPI Integration

```python
from fastapi import HTTPException
from fastapi_orm.exceptions import RecordNotFoundError, ValidationError

@app.post("/users")
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_db)):
    try:
        user = await User.create(session, **data.model_dump())
        return user.to_response()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=e.message)

@app.get("/users/{user_id}")
async def get_user(user_id: int, session: AsyncSession = Depends(get_db)):
    user = await User.get(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_response()
```

Auto Timestamps

Created At and Updated At

```python
from fastapi_orm import DateTimeField

class User(Model):
    __tablename__ = "users"
    
    id: int = IntegerField(primary_key=True)
    username: str = StringField(max_length=100)
    
    # Automatically set on creation
    created_at = DateTimeField(auto_now_add=True)
    
    # Updated automatically on every save
    updated_at = DateTimeField(auto_now=True)
```

Usage

```python
# Create user
user = await User.create(session, username="john")
print(user.created_at)  # 2025-10-21 12:00:00
print(user.updated_at)  # 2025-10-21 12:00:00

# Update user
await user.update_fields(session, username="jane")
print(user.created_at)  # 2025-10-21 12:00:00 (unchanged)
print(user.updated_at)  # 2025-10-21 12:05:00 (updated!)
```

Database Health Checks & Monitoring

Health Check

Comprehensive database health monitoring.

```python
from fastapi import FastAPI
from fastapi_orm import Database

app = FastAPI()
db = Database("postgresql+asyncpg://user:pass@localhost/db")

@app.get("/health")
async def health_check():
    health = await db.health_check()
    return health
    # Returns:
    # {
    #     "status": "healthy",
    #     "response_time_ms": 15.23,
    #     "pool_status": {...},
    #     "database_url": "postgresql+asyncpg://user:****@localhost/db",
    #     "initialized": true
    # }
```

Connection Ping

Simple connectivity test.

```python
if await db.ping():
    print("Database is online")
else:
    print("Database is unreachable")
```

Pool Statistics

Monitor connection pool health.

```python
stats = db.get_pool_status()
print(f"Active connections: {stats['checked_out']}/{stats['pool_size']}")
# Returns: {'pool_size': 5, 'checked_out': 2, 'overflow': 0, 'checked_in': 3}
```

Query Result Caching

High-performance in-memory caching with TTL support.

```python
from fastapi_orm import QueryCache

# Create cache instance
cache = QueryCache(default_ttl=300, max_size=1000)

# Manual caching
cache.set("users:all", users_data, ttl=60)
cached = cache.get("users:all")

# Decorator-based caching
@cache.cached(ttl=120, key_prefix="users")
async def get_all_users(session):
    return await User.all(session)

# Cache statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}%")
```

Cache Management

```python
# Clear specific pattern
cache.clear_pattern("user:")  # Removes all user-related caches

# Cleanup expired entries
expired_count = cache.cleanup_expired()

# Get cache statistics
stats = cache.get_stats()
```

Database Seeding

Powerful seeding utilities for testing and development.

```python
from fastapi_orm import Seeder, random_email, random_username, random_int

seeder = Seeder(db)

# Basic seeding
users = await seeder.seed(User, 100, {
    "username": random_username(),
    "email": random_email(domain="test.com"),
    "age": random_int(18, 80),
    "is_active": True
})

# Factory pattern
seeder.factory("user", lambda i: {
    "username": f"user{i}",
    "email": f"user{i}@example.com",
    "age": random.randint(18, 80)
})

users = await seeder.use_factory("user", User, 50)

# Truncate tables
count = await seeder.truncate(User)
```

Utility Functions

```python
from fastapi_orm import (
    random_string, random_email, random_username,
    random_text, random_int, random_float, 
    random_bool, random_choice, sequential
)

# Use in seeding
products = await seeder.seed(Product, 10, {
    "name": sequential("Product-"),
    "price": random_float(9.99, 99.99),
    "in_stock": random_bool(),
    "category": random_choice(["Electronics", "Clothing", "Books"])
})
```

Composite Constraints

Support for composite primary keys and unique constraints.

```python
from fastapi_orm import (
    Model, IntegerField, StringField,
    create_composite_primary_key,
    create_composite_unique,
    create_composite_index,
    create_check_constraint
)

class UserRole(Model):
    __tablename__ = "user_roles"
    __table_args__ = (
        create_composite_primary_key("user_roles", "user_id", "role_id"),
    )
    
    user_id: int = IntegerField()
    role_id: int = IntegerField()

class Product(Model):
    __tablename__ = "products"
    __table_args__ = (
        create_composite_unique("products", "sku", "warehouse_id"),
        create_composite_index("products", "category", "price"),
        create_check_constraint("products", "price > 0", name="positive_price"),
    )
    
    id: int = IntegerField(primary_key=True)
    sku: str = StringField(max_length=50)
    warehouse_id: int = IntegerField()
    category: str = StringField(max_length=50)
    price: Decimal = DecimalField()
```

Raw SQL Support

Safe parameterized SQL queries.

```python
# Execute raw SQL with parameters
result = await db.execute_raw(
    "SELECT * FROM users WHERE age > :min_age AND status = :status",
    {"min_age": 18, "status": "active"}
)

# Fetch single result as dictionary
user = await db.fetch_one(
    "SELECT * FROM users WHERE id = :id",
    {"id": 123}
)

# Fetch all results as dictionaries
users = await db.fetch_all(
    "SELECT * FROM users WHERE created_at > :date",
    {"date": "2025-01-01"}
)
```

Query Performance Monitoring

Track and analyze query performance.

```python
from fastapi_orm import QueryMonitor

monitor = QueryMonitor(slow_query_threshold=1.0)

# Track queries
async with monitor.track("fetch_users", user_count=100):
    users = await User.all(session)

# Get statistics
stats = monitor.get_stats()
# Returns:
# {
#     "total_queries": 45,
#     "slow_queries": 3,
#     "failed_queries": 0,
#     "avg_duration_ms": 125.5,
#     "max_duration_ms": 1250.0,
#     "min_duration_ms": 15.2
# }

# Analyze slow queries
slow_queries = monitor.get_slow_queries()
for query in slow_queries:
    print(f"{query['name']}: {query['duration_ms']}ms")
```

Complete FastAPI Examples

Basic Application Setup

```python
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_orm import (
    Database, Model, IntegerField, StringField,
    DecimalField, UUIDField, EnumField,
    QueryCache, Seeder, QueryMonitor,
    SoftDeleteMixin, DateTimeField, transactional
)
import enum
import uuid

app = FastAPI()
db = Database("postgresql+asyncpg://user:pass@localhost/db")
cache = QueryCache(default_ttl=300)
monitor = QueryMonitor(slow_query_threshold=0.5)

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Model, SoftDeleteMixin):
    __tablename__ = "users"
    
    id: uuid.UUID = UUIDField(primary_key=True, auto_generate=True)
    username: str = StringField(max_length=50, unique=True)
    email: str = StringField(max_length=255, unique=True)
    role: UserRole = EnumField(UserRole, default=UserRole.USER)
    age: int = IntegerField(min_value=13, max_value=120, nullable=True)
    is_active: bool = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

async def get_db():
    async for session in db.get_session():
        yield session

@app.on_event("startup")
async def startup():
    await db.create_tables()

@app.get("/health")
async def health_check():
    return await db.health_check()

@app.get("/users")
@cache.cached(ttl=60, key_prefix="users")
async def get_users(
    session: AsyncSession = Depends(get_db),
    role: UserRole = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("-created_at")
):
    async with monitor.track("get_users", role=role, page=page):
        filters = {}
        if role:
            filters["role"] = role
        
        result = await User.paginate(
            session,
            page=page,
            page_size=page_size,
            order_by=order_by,
            **filters
        )
        
        return {
            "items": [user.to_response() for user in result["items"]],
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "total_pages": result["total_pages"],
                "has_next": result["has_next"],
                "has_prev": result["has_prev"],
            }
        }

@app.get("/stats")
async def get_stats():
    return {
        "cache": cache.get_stats(),
        "monitor": monitor.get_stats(),
        "pool": db.get_pool_status()
    }

@app.post("/seed")
async def seed_data():
    seeder = Seeder(db)
    users = await seeder.seed(User, 10, {
        "username": lambda i: f"user{i}",
        "email": lambda i: f"user{i}@example.com",
        "role": UserRole.USER,
        "age": random_int(18, 80)
    })
    return {"seeded": len(users)}

@app.post("/users", status_code=201)
async def create_user(
    username: str,
    email: str,
    age: int,
    role: UserRole = UserRole.USER,
    session: AsyncSession = Depends(get_db)
):
    try:
        user = await User.create(
            session, 
            username=username, 
            email=email, 
            age=age,
            role=role
        )
        # Clear user-related cache
        cache.clear_pattern("users")
        return user.to_response()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=e.message)

@app.delete("/users/{user_id}/soft", status_code=204)
async def soft_delete_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    user = await User.get(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.soft_delete(session)
    cache.clear_pattern("users")

@app.post("/users/{user_id}/restore", status_code=200)
async def restore_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    user = await User.get(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.restore(session)
    cache.clear_pattern("users")
    return user.to_response()
```

Migration Guide

From v0.2.0 to v0.3.0

All existing code remains compatible. Simply upgrade and start using new features:

```bash
# Install/upgrade
pip install --upgrade your-fastapi-orm-package

# All existing code works as-is
# Start using new features incrementally
```

Key Benefits of v0.3.0

· No Breaking Changes: Full backward compatibility
· Enhanced Field Types: Decimal, UUID, and Enum support
· Production Monitoring: Health checks and query monitoring
· Performance Optimization: Caching and connection pooling
· Developer Experience: Seeding utilities and better error handling

Performance Improvements

· Caching: 10-100x faster for repeated queries
· Connection Pooling: Better resource management with monitoring
· Query Optimization: Identify and optimize slow queries with QueryMonitor
· Bulk Operations: Faster data manipulation with bulk create/update/delete
· Database Seeding: Rapid test data generation for development

Future Enhancements

Planned features for upcoming releases:

· Redis-backed distributed caching
· Database replication support
· Advanced query optimization hints
· GraphQL integration
· More field types (Array, JSONB, etc.)
· Advanced migration utilities
· Real-time database change notifications

