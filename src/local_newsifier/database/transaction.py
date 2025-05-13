"""Transaction support for database operations."""

from enum import Enum


class JoinTransactionMode(str, Enum):
    """Define how a session should join a transaction.
    
    This enum is used to control transaction behavior when a session is
    passed through dependency injection. It allows for specifying how
    a session should handle transactions in nested contexts.
    
    Attributes:
        CONDITIONAL_SAVEPOINT: Create savepoints when nesting transactions.
        FULL_TRANSACTION: Create a new transaction for each session use.
        NO_TRANSACTION: Do not create transactions automatically.
    """
    CONDITIONAL_SAVEPOINT = "conditional_savepoint"
    FULL_TRANSACTION = "full_transaction"
    NO_TRANSACTION = "no_transaction"