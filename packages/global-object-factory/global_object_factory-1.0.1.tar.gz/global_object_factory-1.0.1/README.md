# Global Object Factory for Python

**Lightweight dependency injection for legacy code. Replace object instantiation with testable factories.**

## Installation

```bash
pip install global-object-factory
```

## Breaking Hard Dependencies

Turn untestable legacy code into testable code by replacing direct instantiation with factory calls.

### The Problem

Legacy code with hard dependencies:

```python
class UserService:
    def process_user(self, user_id):
        # Hard to test - always hits real database
        repo = SqlRepository("server=prod;database=users")
        user = repo.get_user(user_id)
        return user
```

### The Solution

Replace `new` with `create()`:

```python
from global_object_factory import create

class UserService:
    def process_user(self, user_id):
        # Now testable - can inject test doubles
        repo = create(SqlRepository)("server=prod;database=users")
        user = repo.get_user(user_id)
        return user
```

## Writing Tests

### Basic Test Setup

```python
from global_object_factory import create, set_one, context

def test_user_service():
    # Create test double
    mock_repo = MockSqlRepository()
    mock_repo.users = {"123": User("John", "john@example.com")}

    with context():
        # Next create() call returns our mock
        set_one(SqlRepository, mock_repo)

        # Test the code
        service = UserService()
        user = service.process_user("123")

        assert user.name == "John"
```

### Persistent Test Doubles

```python
from global_object_factory import set_always, clear_one

def test_multiple_calls():
    mock_repo = MockSqlRepository()

    with context():
        # All create() calls return our mock
        set_always(SqlRepository, mock_repo)

        service = UserService()
        user1 = service.process_user("123")  # Uses mock
        user2 = service.process_user("456")  # Uses mock too
```

## API Reference

### Core Functions

- `create(cls)` - Returns a factory function for the class
- `create_direct(cls, *args, **kwargs)` - Create instance directly
- `set_one(cls, instance)` - Return test double once, then normal instances
- `set_always(cls, instance)` - Always return test double
- `clear_one(cls)` - Clear test doubles for specific type
- `clear_all()` - Clear all test doubles
- `context()` - Context manager for automatic cleanup

### Advanced Usage

#### Custom Factory Instance

```python
from global_object_factory import ObjectFactory

# Create dedicated factory
api_factory = ObjectFactory()
create_api_service = api_factory.create(ApiService)
service = create_api_service("https://api.example.com")
```

#### Constructor Parameter Tracking

```python
from global_object_factory.interfaces import IConstructorCalledWith, ConstructorParameterInfo
from typing import List

class TrackedService(IConstructorCalledWith):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.constructor_params: List[ConstructorParameterInfo] = []

    def constructor_called_with(self, params: List[ConstructorParameterInfo]) -> None:
        self.constructor_params = params

# Usage
service = create(TrackedService)("localhost", 8080)
print(service.constructor_params[0].name)   # "host"
print(service.constructor_params[0].value)  # "localhost"
```

#### Object Registration

```python
from global_object_factory import register_object, get_registered_object

config = DatabaseConfig()
object_id = register_object(config, "db-config")

# Later retrieve it
retrieved = get_registered_object("db-config")
```

## Requirements

- Python 3.8+
- typing-extensions (for Python < 3.10)

## License

PolyForm Noncommercial License 1.0.0