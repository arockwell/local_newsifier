# Technical Context: Local Newsifier

## Technology Stack

### Backend Technologies
- **Python**: Main programming language
- **FastAPI**: Web framework for the API and web interface
- **SQLModel**: SQL ORM for database interaction
- **PostgreSQL**: Database for persistent storage

### Frontend Technologies
- **Jinja2 Templates**: Server-side rendering for web interface
- **HTML/CSS**: Basic styling and structure
- **Bootstrap**: UI framework for responsive design

### Data Processing
- **Text Processing**: For entity extraction and analysis
- **Sentiment Analysis**: For determining article sentiment
- **Trend Analysis**: For identifying patterns and trends

## Development Environment
- **Poetry**: Dependency management
- **Pytest**: Testing framework
- **GitHub**: Version control

## Deployment
- **Railway**: Cloud platform for application deployment
- **Nixpacks**: Build system used by Railway
- **Uvicorn**: ASGI server for running the FastAPI application

## Database Schema
The database consists of several key tables:
- **articles**: Stores article data
- **entities**: Tracks extracted entities
- **canonical_entities**: Normalized entity references
- **analysis_results**: Stores analysis output

## Key Technical Insights

### SQLModel Parameter Binding
SQLModel's Session.exec() method only takes one parameter (the query itself). Parameters must be bound to the query object before execution using `.bindparams()`:

```python
# Incorrect approach - causes "TypeError: Session.exec() takes 2 positional arguments but 3 were given"
columns = session.exec(query, {"param": value}).all()

# Correct approach
query = query.bindparams(param=value)
columns = session.exec(query).all()
```

### Railway Deployment Configuration
The application is configured for Railway deployment using:
1. **railway.json**: Contains build and deployment settings
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "uvicorn src.local_newsifier.api.main:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 3
     }
   }
   ```

2. **Procfile**: Specifies the web process command
   ```
   web: uvicorn src.local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Environment Variables**: Required for database connection
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - POSTGRES_HOST
   - POSTGRES_PORT
   - POSTGRES_DB
