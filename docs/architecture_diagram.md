# Local Newsifier System Architecture

This document provides a comprehensive overview of the Local Newsifier system architecture, including component relationships, data flow, and interaction patterns.

## Component Architecture Diagram

The following diagram illustrates the major components of the Local Newsifier system and their relationships:

```
+-----------------------------------------------------------------------------------------------------------------+
|                                            LOCAL NEWSIFIER ARCHITECTURE                                           |
+-----------------------------------------------------------------------------------------------------------------+

+-------------------------+      +-------------------------+
|        Entry Points     |      |        API              |
|                         |      |  +-----------------+    |          +-------------------------+
|  +------------------+   |      |  | FastAPI App     |    |          |     Authentication      |
|  | CLI              |   |      |  | - main.py       |<---+--------->| - auth.py               |
|  | - commands/      |   |      |  | - routers/      |    |          | - OAuth2/JWT            |
|  | - feeds.py       |   |      |  | - dependencies.py   |          +-------------------------+
|  | - db.py          |   |      |  +-----------------+    |
|  | - apify.py       |   |      |                         |
|  +------------------+   |      +-------------------------+
+-------------------------+                  ^
            ^                                |
            |                                |
            v                                v
+-------------------------+      +-------------------------+      +-------------------------+
|    Dependency Injection |      |      Flows             |      |       Services          |
|                         |      |                         |      |                         |
|  +------------------+   |      |  +-----------------+    |      |  +-----------------+    |
|  | FastAPI-Injectable   |<---->|  | NewsPipeline    |<---+----->|  | ArticleService  |    |
|  | - providers.py    |   |      |  | EntityTracking  |    |      |  | EntityService   |    |
|  | - injectable       |   |      |  | RSSScrapingFlow |    |      |  | ApifyService    |    |
|  +------------------+   |      |  | TrendAnalysis   |    |      |  | RSSFeedService  |    |
|                         |      |  +-----------------+    |      |  +-----------------+    |
|  +------------------+   |      |                         |      |                         |
|  | Legacy DIContainer   |      +-------------------------+      +-------------------------+
|  | - container.py    |   |                  ^                                ^
|  +------------------+   |                  |                                |
+-------------------------+                  |                                |
            ^                                |                                |
            |                                |                                |
            v                                v                                v
+-------------------------+      +-------------------------+      +-------------------------+
|  Session Management     |      |         Tools           |      |          CRUD          |
|                         |      |                         |      |                         |
|  +------------------+   |      |  +-----------------+    |      |  +-----------------+    |
|  | database/engine.py   |<---->|  | EntityExtractor |    |      |  | ArticleCRUD     |    |
|  | session_utils.py  |   |      |  | EntityResolver  |<---+----->|  | EntityCRUD      |    |
|  | transaction.py    |   |      |  | WebScraper     |    |      |  | RSSFeedCRUD     |    |
|  +------------------+   |      |  | TrendAnalyzer  |    |      |  | ApifySourceCRUD |    |
+-------------------------+      |  +-----------------+    |      |  +-----------------+    |
            ^                    +-------------------------+      |                         |
            |                                                     +-------------------------+
            |                                                                ^
            v                                                                |
+-------------------------------------------------------------------------+
|                               Database Layer                             |
|                                                                         |
|  +-------------------------+     +---------------------------+          |
|  |        Models           |     |      SQLModel ORM         |          |
|  |  +------------------+   |     |  +---------------------+  |          |
|  |  | Article          |   |     |  | Session Factory     |  |          |
|  |  | Entity           |   |<--->|  | Transaction Control |  |          |
|  |  | CanonicalEntity  |   |     |  | Error Handling      |  |          |
|  |  | ApifySourceConfig|   |     |  +---------------------+  |          |
|  |  | RSSFeed          |   |     |                           |          |
|  |  +------------------+   |     +---------------------------+          |
|  +-------------------------+                                            |
+-------------------------------------------------------------------------+
```

## Sequence Diagram: News Pipeline Flow

The following sequence diagram shows the interaction between components during a typical news pipeline operation:

```
+--------+    +-------------+    +-------------+    +----------------+    +----------------+    +-------------+
|  User  |    |  API/CLI    |    |   Flow      |    |   Service      |    |    Tool        |    |    CRUD     |
+--------+    +-------------+    +-------------+    +----------------+    +----------------+    +-------------+
    |               |                 |                   |                     |                    |
    | Request       |                 |                   |                     |                    |
    |-------------->|                 |                   |                     |                    |
    |               | Create DI Deps  |                   |                     |                    |
    |               |---------------->|                   |                     |                    |
    |               |                 | Init State        |                     |                    |
    |               |                 |------------------>|                     |                    |
    |               |                 |                   | Create DB Session   |                    |
    |               |                 |                   |------------------------------------>|    |
    |               |                 |                   |                     |              |    |
    |               |                 |                   | Extract Content     |              |    |
    |               |                 |                   |-------------------->|              |    |
    |               |                 |                   |                     | Process      |    |
    |               |                 |                   |                     |------------->|    |
    |               |                 |                   |                     |              |    |
    |               |                 |                   |                     | Create Article    |
    |               |                 |                   |                     |------------->|    |
    |               |                 |                   |                     |              |    |
    |               |                 |                   |<--------------------|              |    |
    |               |                 |                   | Extract Entities    |              |    |
    |               |                 |                   |-------------------->|              |    |
    |               |                 |                   |                     | Process      |    |
    |               |                 |                   |                     |------------->|    |
    |               |                 |                   |                     | Create Entities   |
    |               |                 |                   |                     |------------->|    |
    |               |                 |                   |                     |              |    |
    |               |                 |<-------------------|                    |              |    |
    |               |                 | Update State      |                     |              |    |
    |               |<----------------|                   |                     |              |    |
    | Response      |                 |                   |                     |              |    |
    |<--------------|                 |                   |                     |              |    |
    |               |                 |                   |                     |              |    |
```

## Component Interaction Diagram

This diagram shows the high-level interactions between system components:

```
                                +----------------+
                                | CLI/API Client |
                                +-------+--------+
                                        |
                                        | HTTP/CLI Commands
                                        v
+----------------+    Injects     +-------------+    FastAPI    +---------------+
| FastAPI        +--------------->|  DI         |<-------------+| Routers       |
| Injectable     |                |  Container  |              || (API Routes)  |
+----------------+                +------+------+              +---------------+
                                         |
                                         | Creates
                                         v
           +------------+         +------+------+         +-------------+
           | Database   |<------->| Service     |<------->| Tools       |
           | Session    |         | Layer       |         | (Processors)|
           +------------+         +------+------+         +-----+-------+
                 ^                       |                       ^
                 |                       | Orchestrates          |
                 |                       v                       |
                 |                +------+------+                |
                 |                | Flow        |                |
                 |                | Components  |                |
                 |                +------+------+                |
                 |                       |                       |
                 |                       | Delegates             |
                 +-----------------------------------------------+
                                         |
                                         | Persists
                                         v
                                  +------+------+
                                  | Database    |
                                  | Models      |
                                  +-------------+
```

## Key Architectural Patterns

### Dependency Injection

The system employs two dependency injection systems:

1. **Legacy DIContainer**
   - Central container for managing dependencies
   - Components register with the container
   - Services retrieve dependencies through the container

2. **FastAPI-Injectable**
   - Newer pattern based on FastAPI's dependency injection
   - Provider functions defined in `src/local_newsifier/di/providers.py`
   - All providers use `use_cache=False` to create fresh instances on each request

### Session Management

Database sessions are managed carefully throughout the system:

- **Context Managers**: Sessions are wrapped in context managers for automatic cleanup
- **Transaction Control**: Explicit transaction boundaries ensure data integrity
- **Error Handling**: Automatic rollback on exceptions

### Flow Orchestration

Flows coordinate multi-step processes:

- **State Management**: Explicit state objects track progress through flows
- **Step Coordination**: Each flow divides work into discrete steps
- **Error Recovery**: Flows incorporate error handling and can resume failed operations

### Service Layer

Services coordinate business logic:

- **Dependency Coordination**: Services combine CRUD operations with tool functionality
- **Transaction Management**: Services establish transaction boundaries
- **Error Classification**: Services classify and handle different types of errors

## Transition Between DI Systems

The project is currently transitioning between two dependency injection systems:

1. **Original custom DIContainer**
   - Components are registered with the container
   - Services get dependencies through the container
   - Used for legacy components

2. **FastAPI-Injectable System**
   - Provider functions define component creation
   - All providers use `use_cache=False` for consistent behavior
   - Being adopted for new and migrated components
