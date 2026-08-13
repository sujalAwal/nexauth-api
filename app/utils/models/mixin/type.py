import uuid
from typing import Optional

from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import CHAR


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses UNIQUEIDENTIFIER for MSSQL, native UUID for PostgreSQL,
    and CHAR(36) for other databases.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID())
        elif dialect.name == "mssql":
            return dialect.type_descriptor(UNIQUEIDENTIFIER())
        else:
            # For MySQL, SQLite, etc. → store as string
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            if dialect.name == "mssql":
                return value  # MSSQL handles UUID objects natively
            return str(value)
        if isinstance(value, str):
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError):
            return value