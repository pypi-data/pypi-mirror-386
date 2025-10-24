"""Storage backend implementations for ThreadStore."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
import re
from datetime import datetime, UTC
import json
import os
from pathlib import Path
import tempfile
import asyncio
from sqlalchemy import create_engine, select, cast, String, text, bindparam
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# Direct imports
from ..models.thread import Thread
from ..models.message import Message
from ..models.attachment import Attachment
from ..storage.file_store import FileStore
from ..utils.logging import get_logger
from .models import Base, ThreadRecord, MessageRecord

logger = get_logger(__name__)

def _sanitize_key(component: str) -> str:
    """Allow only alphanumeric and underscore for JSON path keys to avoid SQL injection."""
    if not re.fullmatch(r"[A-Za-z0-9_]+", component):
        raise ValueError(f"Invalid key component: {component}")
    return component

class StorageBackend(ABC):
    """Abstract base class for thread storage backends."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        pass
    
    @abstractmethod
    async def save(self, thread: Thread) -> Thread:
        """Save a thread to storage."""
        pass
    
    @abstractmethod
    async def get(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        pass
    
    @abstractmethod
    async def delete(self, thread_id: str) -> bool:
        """Delete a thread by ID."""
        pass
    
    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> List[Thread]:
        """List threads with pagination."""
        pass
    
    @abstractmethod
    async def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes."""
        pass
    
    @abstractmethod
    async def find_by_platform(self, platform_name: str, properties: Dict[str, Any]) -> List[Thread]:
        """Find threads by platform name and properties in the platforms structure."""
        pass
    
    @abstractmethod
    async def list_recent(self, limit: Optional[int] = None) -> List[Thread]:
        """List recent threads."""
        pass

    @abstractmethod
    async def find_messages_by_attribute(self, path: str, value: Any) -> Union[List[Message], List[MessageRecord]]:
        """
        Find messages that have a specific attribute at a given JSON path.
        Uses efficient SQL JSON path queries for PostgreSQL and falls back to
        SQLite JSON functions when needed.
        
        Args:
            path: Dot-notation path to the attribute (e.g., "source.platform.attributes.ts")
            value: The value to search for
            
        Returns:
            List of messages matching the criteria (possibly empty)
        """
        pass

class MemoryBackend(StorageBackend):
    """In-memory storage backend using a dictionary."""
    
    def __init__(self):
        self._threads: Dict[str, Thread] = {}
    
    async def initialize(self) -> None:
        pass  # No initialization needed for memory backend
    
    async def save(self, thread: Thread) -> Thread:
        self._threads[thread.id] = thread
        return thread
    
    async def get(self, thread_id: str) -> Optional[Thread]:
        return self._threads.get(thread_id)
    
    async def delete(self, thread_id: str) -> bool:
        if thread_id in self._threads:
            del self._threads[thread_id]
            return True
        return False
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[Thread]:
        threads = sorted(
            self._threads.values(),
            key=lambda t: t.updated_at if hasattr(t, 'updated_at') else t.created_at,
            reverse=True
        )
        return threads[offset:offset + limit]
    
    async def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        matching_threads = []
        for thread in self._threads.values():
            if all(
                thread.attributes.get(k) == v 
                for k, v in attributes.items()
            ):
                matching_threads.append(thread)
        return matching_threads
    
    async def find_by_platform(self, platform_name: str, properties: Dict[str, Any]) -> List[Thread]:
        matching_threads = []
        for thread in self._threads.values():
            platforms = getattr(thread, 'platforms', {})
            if (
                isinstance(platforms, dict) and
                platform_name in platforms and
                all(platforms[platform_name].get(k) == v for k, v in properties.items())
            ):
                matching_threads.append(thread)
        return matching_threads
    
    async def list_recent(self, limit: Optional[int] = None) -> List[Thread]:
        threads = list(self._threads.values())
        threads.sort(key=lambda t: t.updated_at or t.created_at, reverse=True)
        if limit is not None:
            threads = threads[:limit]
        return threads

    async def find_messages_by_attribute(self, path: str, value: Any) -> List[Message]:
        """
        Check if any messages exist with a specific attribute at a given JSON path.
        
        Args:
            path: Dot-notation path to the attribute (e.g., "source.platform.attributes.ts")
            value: The value to search for
            
        Returns:
            List of messages matching the criteria (possibly empty)
        """
        matches: List[Message] = []
        # Traverse all threads and messages
        for thread in self._threads.values():
            for message in thread.messages:
                current: Any = message.model_dump(mode="python")
                # Navigate the nested structure
                parts = [p for p in path.split('.') if p]
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        current = None
                        break
                if current == value:
                    matches.append(message)
        return matches

class SQLBackend(StorageBackend):
    """SQL storage backend supporting both SQLite and PostgreSQL with proper connection pooling."""
    
    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            # Create a temporary directory that persists until program exit
            tmp_dir = Path(tempfile.gettempdir()) / "narrator_threads"
            tmp_dir.mkdir(exist_ok=True)
            database_url = f"sqlite+aiosqlite:///{tmp_dir}/threads.db"
        elif database_url == ":memory:":
            database_url = "sqlite+aiosqlite:///:memory:"
            
        self.database_url = database_url
        
        # Configure engine options with better defaults for connection pooling
        engine_kwargs = {
            'echo': os.environ.get("NARRATOR_DB_ECHO", "").lower() == "true"
        }
        
        # Add pool configuration if not using SQLite
        if not self.database_url.startswith('sqlite'):
            # Default connection pool settings if not specified
            pool_size = int(os.environ.get("NARRATOR_DB_POOL_SIZE", "5"))
            max_overflow = int(os.environ.get("NARRATOR_DB_MAX_OVERFLOW", "10"))
            pool_timeout = int(os.environ.get("NARRATOR_DB_POOL_TIMEOUT", "30"))
            pool_recycle = int(os.environ.get("NARRATOR_DB_POOL_RECYCLE", "300"))
            
            engine_kwargs.update({
                'pool_size': pool_size,
                'max_overflow': max_overflow, 
                'pool_timeout': pool_timeout,
                'pool_recycle': pool_recycle,
                'pool_pre_ping': True  # Check connection validity before using from pool
            })
            
            logger.info(f"Configuring database connection pool: size={pool_size}, "
                       f"max_overflow={max_overflow}, timeout={pool_timeout}, "
                       f"recycle={pool_recycle}")
            
        self.engine = create_async_engine(self.database_url, **engine_kwargs)
        # Create session_maker for database operations
        self._session_maker = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
    @property
    def async_session(self):
        """
        Returns the session factory for creating new database sessions.
        
        Use _get_session() method instead which properly creates a session 
        for each database operation.
        """
        return self._session_maker

    async def initialize(self) -> None:
        """Initialize the database by creating tables if they don't exist."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info(f"Database initialized with tables: {Base.metadata.tables.keys()}")

    def _create_message_from_record(self, msg_record: MessageRecord) -> Message:
        """Helper method to create a Message from a MessageRecord"""
        message = Message(
            id=msg_record.id,
            role=msg_record.role,
            sequence=msg_record.sequence,
            turn=msg_record.turn,
            content=msg_record.content,
            reasoning_content=msg_record.reasoning_content,
            name=msg_record.name,
            tool_call_id=msg_record.tool_call_id,
            tool_calls=msg_record.tool_calls,
            attributes=msg_record.attributes,
            timestamp=msg_record.timestamp,
            source=msg_record.source,
            platforms=msg_record.platforms or {},
            metrics=msg_record.metrics,
            reactions=msg_record.reactions or {}
        )
        if msg_record.attachments:
            message.attachments = [Attachment(**a) for a in msg_record.attachments]
        return message

    def _create_thread_from_record(self, record: ThreadRecord) -> Thread:
        """Helper method to create a Thread from a ThreadRecord"""
        thread = Thread(
            id=record.id,
            title=record.title,
            attributes=record.attributes,
            platforms=record.platforms or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
            messages=[]
        )
        # Sort messages: system messages first, then others by sequence
        sorted_messages = sorted(record.messages, 
            key=lambda m: (0 if m.role == "system" else 1, m.sequence or 0))
        for msg_record in sorted_messages:
            message = self._create_message_from_record(msg_record)
            thread.messages.append(message)
        return thread

    def _create_message_record(self, message: Message, thread_id: str, sequence: int) -> MessageRecord:
        """Helper method to create a MessageRecord from a Message"""
        return MessageRecord(
            id=message.id,
            thread_id=thread_id,
            sequence=sequence,
            turn=message.turn,
            role=message.role,
            content=message.content,
            reasoning_content=message.reasoning_content,
            name=message.name,
            tool_call_id=message.tool_call_id,
            tool_calls=message.tool_calls,
            attributes=message.attributes,
            timestamp=message.timestamp,
            source=message.source,
            platforms=message.platforms,
            attachments=[a.model_dump() for a in message.attachments] if message.attachments else None,
            metrics=message.metrics,
            reactions=message.reactions
        )
    
    async def _get_session(self) -> AsyncSession:
        """Create and return a new session for database operations."""
        return self._session_maker()

    async def _cleanup_failed_attachments(self, thread: Thread) -> None:
        """Helper to clean up attachment files if thread save fails"""
        for message in thread.messages:
            if message.attachments:
                for attachment in message.attachments:
                    if hasattr(attachment, 'cleanup') and callable(attachment.cleanup):
                        await attachment.cleanup()

    async def save(self, thread: Thread) -> Thread:
        """Save a thread and its messages to the database."""
        session = await self._get_session()
        
        # Create a FileStore instance for attachment storage
        file_store = FileStore()
        
        try:
            # Log the platforms data being saved
            logger.info(f"SQLBackend.save: Attempting to save thread {thread.id}. Platforms data: {json.dumps(thread.platforms if thread.platforms is not None else {})}")
            
            # First process and store all attachments
            logger.info(f"Starting to process attachments for thread {thread.id}")
            try:
                for message in thread.messages:
                    if message.attachments:
                        logger.info(f"Processing {len(message.attachments)} attachments for message {message.id}")
                        for attachment in message.attachments:
                            logger.info(f"Processing attachment {attachment.filename} with status {attachment.status}")
                            await attachment.process_and_store(file_store)
                            logger.info(f"Finished processing attachment {attachment.filename}, new status: {attachment.status}")
            except Exception as e:
                # Handle attachment processing failures
                logger.error(f"Failed to process attachment: {str(e)}")
                await self._cleanup_failed_attachments(thread)
                raise RuntimeError(f"Failed to save thread: {str(e)}") from e

            async with session.begin():
                # Get existing thread if it exists
                stmt = select(ThreadRecord).options(selectinload(ThreadRecord.messages)).where(ThreadRecord.id == thread.id)
                result = await session.execute(stmt)
                thread_record = result.scalar_one_or_none()
                
                if thread_record:
                    # Update existing thread
                    thread_record.title = thread.title
                    thread_record.attributes = thread.attributes
                    thread_record.platforms = thread.platforms
                    thread_record.updated_at = datetime.now(UTC)
                    thread_record.messages = []  # Clear existing messages
                else:
                    # Create new thread record
                    thread_record = ThreadRecord(
                        id=thread.id,
                        title=thread.title,
                        attributes=thread.attributes,
                        platforms=thread.platforms,
                        created_at=thread.created_at,
                        updated_at=thread.updated_at,
                        messages=[]
                    )
                
                # Process messages in order
                sequence = 1
                
                # First handle system messages
                for message in thread.messages:
                    if message.role == "system":
                        thread_record.messages.append(self._create_message_record(message, thread.id, 0))
                
                # Then handle non-system messages
                for message in thread.messages:
                    if message.role != "system":
                        thread_record.messages.append(self._create_message_record(message, thread.id, sequence))
                        sequence += 1
                
                session.add(thread_record)
                try:
                    await session.commit()
                    logger.info(f"Thread {thread.id} successfully committed to database.")
                except Exception as e:
                    # Convert database errors to RuntimeError for consistent error handling
                    logger.error(f"Database error during commit: {str(e)}")
                    raise RuntimeError(f"Failed to save thread: Database error - {str(e)}") from e
                return thread
                
        except Exception as e:
            # If this is not already a RuntimeError, wrap it
            if not isinstance(e, RuntimeError):
                raise RuntimeError(f"Failed to save thread: {str(e)}") from e
            raise e
        finally:
            await session.close()

    async def get(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        session = await self._get_session()
        try:
            stmt = select(ThreadRecord).options(selectinload(ThreadRecord.messages)).where(ThreadRecord.id == thread_id)
            result = await session.execute(stmt)
            thread_record = result.scalar_one_or_none()
            return self._create_thread_from_record(thread_record) if thread_record else None
        finally:
            await session.close()

    async def delete(self, thread_id: str) -> bool:
        """Delete a thread by ID."""
        session = await self._get_session()
        try:
            async with session.begin():
                record = await session.get(ThreadRecord, thread_id)
                if record:
                    await session.delete(record)
                    return True
                return False
        finally:
            await session.close()

    async def list(self, limit: int = 100, offset: int = 0) -> List[Thread]:
        """List threads with pagination."""
        session = await self._get_session()
        try:
            result = await session.execute(
                select(ThreadRecord)
                .options(selectinload(ThreadRecord.messages))
                .order_by(ThreadRecord.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return [self._create_thread_from_record(record) for record in result.scalars().all()]
        finally:
            await session.close()

    async def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes."""
        session = await self._get_session()
        try:
            query = select(ThreadRecord).options(selectinload(ThreadRecord.messages))
            
            for key, value in attributes.items():
                if self.database_url.startswith('sqlite'):
                    # Use SQLite json_extract
                    safe_key = _sanitize_key(key)
                    if value is None:
                        query = query.where(text(f"json_extract(attributes, '$.{safe_key}') IS NULL"))
                    elif isinstance(value, bool):
                        # SQLite stores booleans as 1/0
                        num_val = 1 if value else 0
                        query = query.where(text(f"json_extract(attributes, '$.{safe_key}') = {num_val}"))
                    else:
                        query = query.where(
                            text(f"json_extract(attributes, '$.{safe_key}') = :value").bindparams(value=str(value))
                        )
                else:
                    # Use PostgreSQL JSONB operators via text() for direct SQL control
                    logger.info(f"Searching for attribute[{key}] = {value} (type: {type(value)})")
                    
                    # Handle different value types appropriately
                    if value is None:
                        # Check for null/None values
                        safe_key = _sanitize_key(key)
                        query = query.where(text(f"attributes->>'{safe_key}' IS NULL"))
                    else:
                        # Convert value to string for text comparison
                        str_value = str(value)
                        if isinstance(value, bool):
                            # Convert boolean to lowercase string
                            str_value = str(value).lower()
                        
                        # Use PostgreSQL's JSONB operators for direct string comparison
                        safe_key = _sanitize_key(key)
                        param_name = f"attr_{safe_key}"
                        bp = bindparam(param_name, str_value)
                        query = query.where(
                            text(f"attributes->>'{safe_key}' = :{param_name}").bindparams(bp)
                        )
            
            # Log the final query for debugging
            logger.info(f"Executing find_by_attributes query: {query}")
            
            result = await session.execute(query)
            threads = [self._create_thread_from_record(record) for record in result.scalars().all()]
            logger.info(f"Found {len(threads)} matching threads")
            return threads
        except Exception as e:
            logger.error(f"Error in find_by_attributes: {str(e)}")
            raise
        finally:
            await session.close()

    async def find_by_platform(self, platform_name: str, properties: Dict[str, Any]) -> List[Thread]:
        """Find threads by platform name and properties in the platforms structure."""
        session = await self._get_session()
        try:
            query = select(ThreadRecord).options(selectinload(ThreadRecord.messages))
            
            if self.database_url.startswith('sqlite'):
                # Use SQLite json_extract for platform name
                safe_platform = _sanitize_key(platform_name)
                query = query.where(text(f"json_extract(platforms, '$.{safe_platform}') IS NOT NULL"))
                # Add property conditions
                for key, value in properties.items():
                    # Convert value to string for text comparison
                    safe_key = _sanitize_key(key)
                    if value is None:
                        query = query.where(text(f"json_extract(platforms, '$.{safe_platform}.{safe_key}') IS NULL"))
                    elif isinstance(value, bool):
                        num_val = 1 if value else 0
                        query = query.where(text(f"json_extract(platforms, '$.{safe_platform}.{safe_key}') = {num_val}"))
                    else:
                        str_value = str(value)
                        param_name = f"value_{safe_platform}_{safe_key}" # Ensure unique param name
                        bp = bindparam(param_name, str_value)
                        query = query.where(
                            text(f"json_extract(platforms, '$.{safe_platform}.{safe_key}') = :{param_name}")
                            .bindparams(bp)
                        )
            else:
                # Use PostgreSQL JSONB operators for platform checks
                safe_platform = _sanitize_key(platform_name)
                query = query.where(text(f"platforms ? '{safe_platform}'"))
                
                # Add property conditions with text() for proper PostgreSQL JSONB syntax
                for key, value in properties.items():
                    str_value = str(value)
                    safe_key = _sanitize_key(key)
                    param_name = f"value_{safe_platform}_{safe_key}"
                    bp = bindparam(param_name, str_value)
                    query = query.where(
                        text(f"platforms->'{safe_platform}'->>'{safe_key}' = :{param_name}")
                        .bindparams(bp)
                    )
            
            result = await session.execute(query)
            return [self._create_thread_from_record(record) for record in result.scalars().all()]
        finally:
            await session.close()

    async def list_recent(self, limit: Optional[int] = None) -> List[Thread]:
        """List recent threads."""
        session = await self._get_session()
        try:
            query = select(ThreadRecord).options(selectinload(ThreadRecord.messages)).order_by(ThreadRecord.updated_at.desc())
            if limit is not None:
                query = query.limit(limit)
            result = await session.execute(query)
            return [self._create_thread_from_record(record) for record in result.scalars().all()]
        finally:
            await session.close()

    async def find_messages_by_attribute(self, path: str, value: Any) -> List[MessageRecord]:
        """
        Find messages that have a specific attribute at a given JSON path.
        Uses efficient SQL JSON path queries for PostgreSQL and falls back to
        SQLite JSON functions when needed.
        
        Args:
            path: Dot-notation path to the attribute (e.g., "source.platform.attributes.ts")
            value: The value to search for
            
        Returns:
            List of messages matching the criteria (possibly empty)
        """
        session = await self._get_session()
        try:
            query = select(MessageRecord)
            
            # Normalize and sanitize path parts
            parts = [p for p in path.split('.') if p]
            parts = [_sanitize_key(p) for p in parts]
            if not parts:
                return []
            # Support paths prefixed with 'source.' by stripping the leading component
            if parts and parts[0] == 'source':
                parts = parts[1:]
                if not parts:
                    return []
            if self.database_url.startswith('sqlite'):
                # Use SQLite json_extract with a proper JSON path: $.a.b.c (safe due to sanitized parts)
                json_path = '$.' + '.'.join(parts)
                query = query.where(
                    text(f"json_extract(source, '{json_path}') = :value").bindparams(value=str(value))
                )
            else:
                # Use PostgreSQL JSONB operators: source->'a'->'b'->>'c' (last part text)
                if len(parts) == 1:
                    pg_expr = f"source->>'{parts[0]}'"
                else:
                    head = parts[:-1]
                    tail = parts[-1]
                    pg_expr = "source" + ''.join([f"->'{h}'" for h in head]) + f"->>'{tail}'"
                query = query.where(
                    text(f"{pg_expr} = :value").bindparams(value=str(value))
                )
            
            result = await session.execute(query)
            return result.scalars().all()
        finally:
            await session.close()

    async def get_thread_by_message_id(self, message_id: str) -> Optional[Thread]:
        """
        Find a thread containing a specific message ID.
        
        Args:
            message_id: The ID of the message to find
            
        Returns:
            The Thread containing the message, or None if not found
        """
        session = await self._get_session()
        try:
            # Query for the message and join with thread
            stmt = (
                select(ThreadRecord)
                .options(selectinload(ThreadRecord.messages))
                .join(MessageRecord)
                .where(MessageRecord.id == message_id)
            )
            result = await session.execute(stmt)
            thread_record = result.scalar_one_or_none()
            return self._create_thread_from_record(thread_record) if thread_record else None
        finally:
            await session.close() 