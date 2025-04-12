"""Database configuration settings."""
from typing import Optional, Any
from pydantic import BaseSettings, PostgresDsn, validator
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

def get_database() -> Engine:
    """Get database engine instance.
    
    Returns:
        SQLAlchemy engine instance
    """
    settings = DatabaseSettings()
    return init_db(str(settings.DATABASE_URL))

def get_db_session() -> sessionmaker:
    """Get database session factory.
    
    Returns:
        SQLAlchemy session factory
    """
    engine = get_database()
    return get_session(engine) 