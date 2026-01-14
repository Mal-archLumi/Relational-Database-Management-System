"""
Custom exceptions for MALDB
"""

class DatabaseError(Exception):
    """Base exception for all database errors"""
    pass

class ParseError(DatabaseError):
    """SQL parsing error"""
    pass

class ExecutionError(DatabaseError):
    """Query execution error"""
    pass

class StorageError(DatabaseError):
    """Storage layer error"""
    pass

class ConstraintError(DatabaseError):
    """Constraint violation error"""
    pass

class EncryptionError(DatabaseError):
    """Encryption/decryption error"""
    pass

class TransactionError(DatabaseError):
    """Transaction-related error"""
    pass