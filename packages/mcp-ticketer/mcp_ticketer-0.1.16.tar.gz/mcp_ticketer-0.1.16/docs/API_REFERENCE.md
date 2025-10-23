# MCP Ticketer API Reference

Complete API reference for MCP Ticketer's core models, adapters, and server interfaces.

## Table of Contents

- [Core Models](#core-models)
- [BaseAdapter Interface](#baseadapter-interface)
- [Adapter Registry API](#adapter-registry-api)
- [Cache API](#cache-api)
- [MCP Server API](#mcp-server-api)
- [CLI API](#cli-api)
- [Type Definitions](#type-definitions)
- [Error Handling](#error-handling)

## Core Models

### BaseTicket

Base class for all ticket types with common fields and validation.

```python
from mcp_ticketer.core.models import BaseTicket, TicketState, Priority
from typing import Optional, Dict, Any, List
from datetime import datetime

class BaseTicket(BaseModel):
    """Base model for all ticket types."""

    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    state: TicketState = TicketState.OPEN
    priority: Priority = Priority.MEDIUM
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `Optional[str]` | `None` | Unique identifier, populated by adapters |
| `title` | `str` | *Required* | Ticket title (1-255 characters) |
| `description` | `Optional[str]` | `None` | Detailed description |
| `state` | `TicketState` | `OPEN` | Current workflow state |
| `priority` | `Priority` | `MEDIUM` | Priority level |
| `tags` | `List[str]` | `[]` | List of tags/labels |
| `created_at` | `Optional[datetime]` | `None` | Creation timestamp |
| `updated_at` | `Optional[datetime]` | `None` | Last update timestamp |
| `metadata` | `Dict[str, Any]` | `{}` | System-specific metadata |

**Example:**
```python
ticket = BaseTicket(
    title="Fix authentication bug",
    description="Users cannot login with SSO",
    priority=Priority.HIGH,
    tags=["bug", "auth", "security"]
)
```

### Task

Individual work item extending BaseTicket with task-specific fields.

```python
class Task(BaseTicket):
    """Task - individual work item."""

    ticket_type: str = "task"  # Immutable
    parent_issue: Optional[str] = None
    parent_epic: Optional[str] = None
    assignee: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
```

**Additional Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ticket_type` | `str` | `"task"` | Type identifier (frozen) |
| `parent_issue` | `Optional[str]` | `None` | Parent issue ID |
| `parent_epic` | `Optional[str]` | `None` | Parent epic ID |
| `assignee` | `Optional[str]` | `None` | Assigned user |
| `estimated_hours` | `Optional[float]` | `None` | Time estimate |
| `actual_hours` | `Optional[float]` | `None` | Actual time spent |

**Example:**
```python
task = Task(
    title="Implement JWT authentication",
    description="Replace session-based auth with JWT tokens",
    assignee="john.doe@company.com",
    estimated_hours=8.0,
    parent_epic="epic-auth-system",
    tags=["backend", "security"]
)
```

### Epic

High-level container for related tasks and issues.

```python
class Epic(BaseTicket):
    """Epic - highest level container for work."""

    ticket_type: str = "epic"  # Immutable
    child_issues: List[str] = []
```

**Additional Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ticket_type` | `str` | `"epic"` | Type identifier (frozen) |
| `child_issues` | `List[str]` | `[]` | IDs of child issues |

**Example:**
```python
epic = Epic(
    title="User Authentication System",
    description="Complete overhaul of authentication system",
    priority=Priority.HIGH,
    child_issues=["task-jwt-impl", "task-oauth-integration"]
)
```

### Comment

Comments and discussions on tickets.

```python
class Comment(BaseModel):
    """Comment on a ticket."""

    id: Optional[str] = None
    ticket_id: str
    author: Optional[str] = None
    content: str
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `Optional[str]` | `None` | Comment ID |
| `ticket_id` | `str` | *Required* | Parent ticket ID |
| `author` | `Optional[str]` | `None` | Comment author |
| `content` | `str` | *Required* | Comment text (min 1 char) |
| `created_at` | `Optional[datetime]` | `None` | Creation timestamp |
| `metadata` | `Dict[str, Any]` | `{}` | System metadata |

**Example:**
```python
comment = Comment(
    ticket_id="TASK-123",
    author="jane.doe@company.com",
    content="I've started working on this. ETA is 2 days."
)
```

### SearchQuery

Query parameters for searching tickets.

```python
class SearchQuery(BaseModel):
    """Search query parameters."""

    query: Optional[str] = None
    state: Optional[TicketState] = None
    priority: Optional[Priority] = None
    tags: Optional[List[str]] = None
    assignee: Optional[str] = None
    limit: int = 10
    offset: int = 0
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | `Optional[str]` | `None` | Text search query |
| `state` | `Optional[TicketState]` | `None` | Filter by state |
| `priority` | `Optional[Priority]` | `None` | Filter by priority |
| `tags` | `Optional[List[str]]` | `None` | Filter by tags |
| `assignee` | `Optional[str]` | `None` | Filter by assignee |
| `limit` | `int` | `10` | Max results (1-100) |
| `offset` | `int` | `0` | Result offset (≥0) |

**Example:**
```python
search_query = SearchQuery(
    query="authentication",
    state=TicketState.OPEN,
    priority=Priority.HIGH,
    tags=["security", "backend"],
    limit=25
)
```

### Enumerations

#### TicketState

```python
class TicketState(str, Enum):
    """Universal ticket states with state machine."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    TESTED = "tested"
    DONE = "done"
    WAITING = "waiting"
    BLOCKED = "blocked"
    CLOSED = "closed"

    @classmethod
    def valid_transitions(cls) -> Dict[str, List[str]]:
        """Get valid state transitions."""
        return {
            cls.OPEN: [cls.IN_PROGRESS, cls.WAITING, cls.BLOCKED, cls.CLOSED],
            cls.IN_PROGRESS: [cls.READY, cls.WAITING, cls.BLOCKED, cls.OPEN],
            cls.READY: [cls.TESTED, cls.IN_PROGRESS, cls.BLOCKED],
            cls.TESTED: [cls.DONE, cls.IN_PROGRESS],
            cls.DONE: [cls.CLOSED],
            cls.WAITING: [cls.OPEN, cls.IN_PROGRESS, cls.CLOSED],
            cls.BLOCKED: [cls.OPEN, cls.IN_PROGRESS, cls.CLOSED],
            cls.CLOSED: [],
        }

    def can_transition_to(self, target: "TicketState") -> bool:
        """Check if transition is valid."""
        return target.value in self.valid_transitions().get(self, [])
```

**Valid State Transitions:**
- `OPEN` → `IN_PROGRESS`, `WAITING`, `BLOCKED`, `CLOSED`
- `IN_PROGRESS` → `READY`, `WAITING`, `BLOCKED`, `OPEN`
- `READY` → `TESTED`, `IN_PROGRESS`, `BLOCKED`
- `TESTED` → `DONE`, `IN_PROGRESS`
- `DONE` → `CLOSED`
- `WAITING` → `OPEN`, `IN_PROGRESS`, `CLOSED`
- `BLOCKED` → `OPEN`, `IN_PROGRESS`, `CLOSED`
- `CLOSED` → *(no transitions)*

#### Priority

```python
class Priority(str, Enum):
    """Universal priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

## BaseAdapter Interface

Abstract base class that all ticket system adapters must implement.

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic

T = TypeVar("T", Epic, Task)

class BaseAdapter(ABC, Generic[T]):
    """Abstract base class for all ticket system adapters."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize adapter with configuration."""
        self.config = config
        self._state_mapping = self._get_state_mapping()

    @abstractmethod
    def _get_state_mapping(self) -> Dict[TicketState, str]:
        """Get mapping from universal states to system-specific states."""
        pass

    # CRUD Operations
    @abstractmethod
    async def create(self, ticket: T) -> T:
        """Create a new ticket."""
        pass

    @abstractmethod
    async def read(self, ticket_id: str) -> Optional[T]:
        """Read a ticket by ID."""
        pass

    @abstractmethod
    async def update(self, ticket_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """Update a ticket."""
        pass

    @abstractmethod
    async def delete(self, ticket_id: str) -> bool:
        """Delete a ticket."""
        pass

    # Query Operations
    @abstractmethod
    async def list(
        self,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """List tickets with pagination and filters."""
        pass

    @abstractmethod
    async def search(self, query: SearchQuery) -> List[T]:
        """Search tickets using advanced query."""
        pass

    # State Management
    @abstractmethod
    async def transition_state(
        self,
        ticket_id: str,
        target_state: TicketState
    ) -> Optional[T]:
        """Transition ticket to a new state."""
        pass

    async def validate_transition(
        self,
        ticket_id: str,
        target_state: TicketState
    ) -> bool:
        """Validate if state transition is allowed."""
        ticket = await self.read(ticket_id)
        if not ticket:
            return False
        current_state = ticket.state
        if isinstance(current_state, str):
            current_state = TicketState(current_state)
        return current_state.can_transition_to(target_state)

    # Comment Operations
    @abstractmethod
    async def add_comment(self, comment: Comment) -> Comment:
        """Add a comment to a ticket."""
        pass

    @abstractmethod
    async def get_comments(
        self,
        ticket_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Comment]:
        """Get comments for a ticket."""
        pass

    # State Mapping Utilities
    def map_state_to_system(self, state: TicketState) -> str:
        """Map universal state to system-specific state."""
        return self._state_mapping.get(state, state.value)

    def map_state_from_system(self, system_state: str) -> TicketState:
        """Map system-specific state to universal state."""
        reverse_mapping = {v: k for k, v in self._state_mapping.items()}
        return reverse_mapping.get(system_state, TicketState.OPEN)

    # Lifecycle
    async def close(self) -> None:
        """Close adapter and cleanup resources."""
        pass
```

### Usage Example

```python
from mcp_ticketer.adapters.linear import LinearAdapter

# Initialize adapter
config = {
    "team_id": "team-abc123",
    "api_key": "lin_api_def456"
}
adapter = LinearAdapter(config)

# Create a task
task = Task(
    title="Fix login bug",
    priority=Priority.HIGH,
    tags=["bug", "auth"]
)
created_task = await adapter.create(task)
print(f"Created: {created_task.id}")

# Read task
task = await adapter.read(created_task.id)
if task:
    print(f"State: {task.state}")

# Update task
updated = await adapter.update(created_task.id, {
    "assignee": "developer@company.com",
    "priority": Priority.CRITICAL
})

# Transition state
transitioned = await adapter.transition_state(
    created_task.id,
    TicketState.IN_PROGRESS
)

# Search tasks
results = await adapter.search(SearchQuery(
    query="login",
    state=TicketState.IN_PROGRESS
))

# Cleanup
await adapter.close()
```

## Adapter Registry API

Dynamic registry for managing adapter instances.

```python
from mcp_ticketer.core.registry import AdapterRegistry
from typing import Dict, Type, Any, Optional

class AdapterRegistry:
    """Registry for managing ticket system adapters."""

    @classmethod
    def register(cls, name: str, adapter_class: Type[BaseAdapter]) -> None:
        """Register an adapter class."""
        pass

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister an adapter."""
        pass

    @classmethod
    def get_adapter(
        cls,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        force_new: bool = False
    ) -> BaseAdapter:
        """Get or create an adapter instance."""
        pass

    @classmethod
    def list_adapters(cls) -> Dict[str, Type[BaseAdapter]]:
        """List all registered adapters."""
        pass

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if an adapter is registered."""
        pass

    @classmethod
    async def close_all(cls) -> None:
        """Close all adapter instances and clear cache."""
        pass

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registrations and instances."""
        pass
```

### Usage Example

```python
# Register custom adapter
from mypackage.adapters import CustomAdapter
AdapterRegistry.register("custom", CustomAdapter)

# Get adapter instance
config = {"api_key": "secret"}
adapter = AdapterRegistry.get_adapter("custom", config)

# List available adapters
adapters = AdapterRegistry.list_adapters()
print(f"Available: {list(adapters.keys())}")

# Check if registered
if AdapterRegistry.is_registered("linear"):
    linear_adapter = AdapterRegistry.get_adapter("linear", linear_config)

# Cleanup
await AdapterRegistry.close_all()
```

## Cache API

In-memory cache with TTL support for performance optimization.

```python
from mcp_ticketer.cache.memory import MemoryCache, cache_decorator
from typing import Optional, Any, Callable
import time

class MemoryCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, default_ttl: float = 300.0):
        """Initialize cache with default TTL (5 minutes)."""
        pass

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ) -> None:
        """Set value in cache."""
        pass

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    async def clear(self) -> None:
        """Clear all cache entries."""
        pass

    async def cleanup_expired(self) -> int:
        """Remove expired entries."""
        pass

    def size(self) -> int:
        """Get number of entries in cache."""
        pass

    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """Generate cache key from arguments."""
        pass
```

### Cache Decorator

```python
def cache_decorator(
    ttl: Optional[float] = None,
    key_prefix: str = "",
    cache_instance: Optional[MemoryCache] = None
) -> Callable:
    """Decorator for caching async function results."""
    pass
```

### Usage Example

```python
# Manual cache usage
cache = MemoryCache(default_ttl=600)  # 10 minutes

# Cache a value
await cache.set("user:123", user_data, ttl=300)

# Retrieve from cache
user = await cache.get("user:123")
if user is None:
    user = await fetch_user_from_db(123)
    await cache.set("user:123", user)

# Decorator usage
@cache_decorator(ttl=300, key_prefix="tickets")
async def get_ticket(ticket_id: str) -> Optional[Task]:
    return await expensive_ticket_lookup(ticket_id)

# Cache statistics
print(f"Cache size: {cache.size()}")
expired_count = await cache.cleanup_expired()
print(f"Cleaned up {expired_count} expired entries")

# Generate cache key
key = MemoryCache.generate_key("user", 123, active=True)
```

## MCP Server API

JSON-RPC server implementation for AI tool integration.

```python
from mcp_ticketer.mcp.server import MCPTicketServer
from typing import Any, Dict, Optional

class MCPTicketServer:
    """MCP server for ticket operations over stdio."""

    def __init__(
        self,
        adapter_type: str = "aitrackdown",
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize MCP server."""
        pass

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC request."""
        pass

    async def run(self) -> None:
        """Run the MCP server, reading from stdin and writing to stdout."""
        pass

    async def stop(self) -> None:
        """Stop the server."""
        pass
```

### JSON-RPC Methods

#### `ticket/create`
Create a new ticket.

**Parameters:**
```python
{
    "title": str,              # Required
    "description": str,        # Optional
    "priority": str,           # Optional: "low", "medium", "high", "critical"
    "tags": List[str],         # Optional
    "assignee": str            # Optional
}
```

**Response:**
```python
{
    "id": str,
    "title": str,
    "state": str,
    "priority": str,
    "created_at": str,         # ISO timestamp
    "updated_at": str,         # ISO timestamp
    "metadata": Dict[str, Any]
}
```

#### `ticket/read`
Read a ticket by ID.

**Parameters:**
```python
{
    "ticket_id": str           # Required
}
```

**Response:** Task object or `null` if not found.

#### `ticket/update`
Update ticket properties.

**Parameters:**
```python
{
    "ticket_id": str,          # Required
    "updates": {               # Required
        "title": str,          # Optional
        "description": str,    # Optional
        "priority": str,       # Optional
        "assignee": str        # Optional
    }
}
```

**Response:** Updated Task object or `null` if failed.

#### `ticket/delete`
Delete a ticket.

**Parameters:**
```python
{
    "ticket_id": str           # Required
}
```

**Response:** `boolean` - true if deleted.

#### `ticket/list`
List tickets with filters.

**Parameters:**
```python
{
    "limit": int,              # Optional, default: 10
    "offset": int,             # Optional, default: 0
    "filters": {               # Optional
        "state": str,
        "priority": str,
        "assignee": str
    }
}
```

**Response:** Array of Task objects.

#### `ticket/search`
Advanced ticket search.

**Parameters:**
```python
{
    "query": str,              # Optional text search
    "state": str,              # Optional state filter
    "priority": str,           # Optional priority filter
    "assignee": str,           # Optional assignee filter
    "tags": List[str],         # Optional tag filters
    "limit": int               # Optional, default: 10
}
```

**Response:** Array of Task objects.

#### `ticket/transition`
Transition ticket state.

**Parameters:**
```python
{
    "ticket_id": str,          # Required
    "target_state": str        # Required
}
```

**Response:** Updated Task object or `null` if invalid transition.

#### `ticket/comment`
Manage comments.

**Parameters for adding:**
```python
{
    "operation": "add",
    "ticket_id": str,          # Required
    "content": str,            # Required
    "author": str              # Optional
}
```

**Parameters for listing:**
```python
{
    "operation": "list",
    "ticket_id": str,          # Required
    "limit": int,              # Optional, default: 10
    "offset": int              # Optional, default: 0
}
```

**Response:** Comment object (add) or array of Comments (list).

#### `tools/list`
List available MCP tools.

**Parameters:** None

**Response:** Tool definitions for AI integration.

### Usage Example

```python
# Initialize server
server = MCPTicketServer(
    adapter_type="linear",
    config={"team_id": "team123", "api_key": "lin_api_xxx"}
)

# Run server (blocks until stopped)
await server.run()

# Or handle individual requests
request = {
    "jsonrpc": "2.0",
    "method": "ticket/create",
    "params": {
        "title": "New feature request",
        "priority": "high"
    },
    "id": 1
}

response = await server.handle_request(request)
print(response)
```

## CLI API

Command-line interface built with Typer.

```python
from mcp_ticketer.cli.main import app
import typer

# Main CLI app
app = typer.Typer(
    name="mcp-ticket",
    help="Universal ticket management interface"
)

# Configuration management
def load_config() -> dict:
    """Load configuration from file."""
    pass

def save_config(config: dict) -> None:
    """Save configuration to file."""
    pass

def get_adapter():
    """Get configured adapter instance."""
    pass
```

### Commands

#### `init`
Initialize configuration.

```python
@app.command()
def init(
    adapter: AdapterType = typer.Option(..., "--adapter", "-a"),
    # ... adapter-specific options
) -> None:
    """Initialize MCP Ticketer configuration."""
    pass
```

#### `create`
Create a new ticket.

```python
@app.command()
def create(
    title: str = typer.Argument(...),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    priority: Priority = typer.Option(Priority.MEDIUM, "--priority", "-p"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a"),
) -> None:
    """Create a new ticket."""
    pass
```

#### `list`
List tickets.

```python
@app.command("list")
def list_tickets(
    state: Optional[TicketState] = typer.Option(None, "--state", "-s"),
    priority: Optional[Priority] = typer.Option(None, "--priority", "-p"),
    limit: int = typer.Option(10, "--limit", "-l"),
) -> None:
    """List tickets with optional filters."""
    pass
```

#### `show`
Show ticket details.

```python
@app.command()
def show(
    ticket_id: str = typer.Argument(...),
    comments: bool = typer.Option(False, "--comments", "-c"),
) -> None:
    """Show detailed ticket information."""
    pass
```

#### `update`
Update ticket.

```python
@app.command()
def update(
    ticket_id: str = typer.Argument(...),
    title: Optional[str] = typer.Option(None, "--title"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    priority: Optional[Priority] = typer.Option(None, "--priority", "-p"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a"),
) -> None:
    """Update ticket fields."""
    pass
```

#### `transition`
Change ticket state.

```python
@app.command()
def transition(
    ticket_id: str = typer.Argument(...),
    state: TicketState = typer.Argument(...),
) -> None:
    """Change ticket state with validation."""
    pass
```

#### `search`
Search tickets.

```python
@app.command()
def search(
    query: Optional[str] = typer.Argument(None),
    state: Optional[TicketState] = typer.Option(None, "--state", "-s"),
    priority: Optional[Priority] = typer.Option(None, "--priority", "-p"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a"),
    limit: int = typer.Option(10, "--limit", "-l"),
) -> None:
    """Search tickets with advanced query."""
    pass
```

### Usage Example

```python
# Programmatic usage
from mcp_ticketer.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()

# Test create command
result = runner.invoke(app, [
    "create", "Test ticket",
    "--priority", "high",
    "--tag", "test",
    "--assignee", "user@example.com"
])

print(result.stdout)
```

## Type Definitions

### Custom Types

```python
from typing import TypeVar, Union, Dict, Any, List, Optional
from datetime import datetime

# Generic type for tickets
T = TypeVar("T", Epic, Task)

# Adapter type variable
AdapterType = TypeVar("AdapterType", bound=BaseAdapter)

# Configuration dictionary
ConfigDict = Dict[str, Any]

# Metadata dictionary
MetadataDict = Dict[str, Any]

# Update dictionary for ticket updates
UpdateDict = Dict[str, Union[str, int, float, bool, List[str], datetime]]

# Filter dictionary for queries
FilterDict = Dict[str, Union[str, int, bool, List[str]]]
```

### Protocol Definitions

```python
from typing import Protocol, runtime_checkable, List, Optional
from abc import abstractmethod

@runtime_checkable
class TicketProvider(Protocol):
    """Protocol for objects that can provide tickets."""

    async def get_tickets(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Task]:
        """Get tickets from the provider."""
        ...

@runtime_checkable
class CommentProvider(Protocol):
    """Protocol for objects that can provide comments."""

    async def get_comments(
        self,
        ticket_id: str,
        limit: int = 10
    ) -> List[Comment]:
        """Get comments for a ticket."""
        ...

@runtime_checkable
class StateValidator(Protocol):
    """Protocol for state validation."""

    def can_transition_to(self, target_state: TicketState) -> bool:
        """Check if transition is valid."""
        ...
```

### Utility Functions

```python
from typing import Type, TypeGuard
from mcp_ticketer.core.models import BaseTicket, Task, Epic

def is_task(ticket: BaseTicket) -> TypeGuard[Task]:
    """Type guard to check if ticket is a Task."""
    return ticket.ticket_type == "task"

def is_epic(ticket: BaseTicket) -> TypeGuard[Epic]:
    """Type guard to check if ticket is an Epic."""
    return ticket.ticket_type == "epic"

def validate_ticket_id(ticket_id: str) -> bool:
    """Validate ticket ID format."""
    return bool(ticket_id and len(ticket_id.strip()) > 0)

def sanitize_title(title: str) -> str:
    """Sanitize ticket title."""
    return title.strip()[:255]
```

## Error Handling

### Exception Hierarchy

```python
class MCPTicketerError(Exception):
    """Base exception for MCP Ticketer."""
    pass

class AdapterError(MCPTicketerError):
    """Base adapter error."""

    def __init__(
        self,
        message: str,
        adapter_name: str,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.adapter_name = adapter_name
        self.original_error = original_error

class AuthenticationError(AdapterError):
    """Authentication failed with external service."""
    pass

class RateLimitError(AdapterError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        adapter_name: str,
        retry_after: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, adapter_name, original_error)
        self.retry_after = retry_after

class ValidationError(MCPTicketerError):
    """Data validation error."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None
    ):
        super().__init__(message)
        self.field = field
        self.value = value

class ConfigurationError(MCPTicketerError):
    """Configuration error."""
    pass

class CacheError(MCPTicketerError):
    """Cache operation error."""
    pass

class StateTransitionError(MCPTicketerError):
    """Invalid state transition."""

    def __init__(
        self,
        message: str,
        from_state: TicketState,
        to_state: TicketState
    ):
        super().__init__(message)
        self.from_state = from_state
        self.to_state = to_state
```

### Error Handling Examples

```python
from mcp_ticketer.core.models import Task, TicketState
from mcp_ticketer.adapters.linear import LinearAdapter
from mcp_ticketer.exceptions import (
    AuthenticationError,
    RateLimitError,
    StateTransitionError,
    ValidationError
)

async def robust_ticket_creation():
    """Example of robust error handling."""
    try:
        adapter = LinearAdapter(config)

        task = Task(
            title="New feature",
            priority=Priority.HIGH
        )

        created = await adapter.create(task)
        return created

    except AuthenticationError as e:
        print(f"Auth failed for {e.adapter_name}: {e}")
        # Handle re-authentication

    except RateLimitError as e:
        print(f"Rate limited: {e}")
        if e.retry_after:
            await asyncio.sleep(e.retry_after)
            # Retry logic

    except ValidationError as e:
        print(f"Validation failed for field {e.field}: {e}")
        # Fix validation issue

    except AdapterError as e:
        print(f"Adapter error in {e.adapter_name}: {e}")
        if e.original_error:
            print(f"Original: {e.original_error}")

async def safe_state_transition():
    """Example of safe state transitions."""
    try:
        # Validate before attempting
        if await adapter.validate_transition("TASK-123", TicketState.DONE):
            result = await adapter.transition_state("TASK-123", TicketState.DONE)
            return result
        else:
            print("Invalid transition")
            return None

    except StateTransitionError as e:
        print(f"Cannot transition from {e.from_state} to {e.to_state}")
        # Show valid transitions
        valid = e.from_state.valid_transitions().get(e.from_state, [])
        print(f"Valid transitions: {valid}")
```

---

This API reference provides comprehensive documentation for all public interfaces in MCP Ticketer. For implementation examples and advanced usage patterns, see the [Developer Guide](DEVELOPER_GUIDE.md).