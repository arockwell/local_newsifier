"""Database configuration settings."""
from typing import Optional, Any
from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from ..models.database import init_db, get_session

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str
    
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, Any]) -> Any:
        """Assemble database connection URL.
        
        Args:
            v: Optional database URL
            values: Other settings values
            
        Returns:
            Assembled database URL
        """
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB')}",
        )

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True

def get_database(env_file: str = ".env") -> Engine:
    """Get database engine instance.
    
    Args:
        env_file: Environment file to use
        
    Returns:
        SQLAlchemy engine instance
    """
    settings = DatabaseSettings(_env_file=env_file)
    return init_db(str(settings.DATABASE_URL))

def get_db_session(env_file: str = ".env") -> sessionmaker:
    """Get database session factory.
    
    Args:
        env_file: Environment file to use
        
    Returns:
        SQLAlchemy session factory
    """
    engine = get_database(env_file)
    return get_session(engine) 