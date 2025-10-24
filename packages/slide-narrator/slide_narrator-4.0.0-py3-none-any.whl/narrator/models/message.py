from typing import Dict, Optional, Literal, Any, Union, List
from typing_extensions import TypedDict
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import json
from narrator.utils.logging import get_logger
import base64
# Direct imports
from narrator.models.attachment import Attachment
from narrator.storage.file_store import FileStore

# Get configured logger
logger = get_logger(__name__)

class ImageUrl(TypedDict):
    url: str

class ImageContent(TypedDict):
    type: Literal["image_url"]
    image_url: ImageUrl

class TextContent(TypedDict):
    type: Literal["text"]
    text: str

class EntitySource(TypedDict, total=False):
    id: str  # Unique identifier for the entity
    name: str  # Human-readable name of the entity
    type: Literal["user", "agent", "tool"]  # Type of entity
    attributes: Optional[Dict[str, Any]]  # All other entity-specific attributes

class Message(BaseModel):
    """Represents a single message in a thread"""
    id: str = None  # Will be set in __init__
    role: Literal["system", "user", "assistant", "tool"]
    sequence: Optional[int] = Field(
        default=None,
        description="Message sequence number within thread. System messages get lowest sequences."
    )
    turn: Optional[int] = Field(
        default=None,
        description="Turn number grouping related messages in the same conversational step."
    )
    content: Optional[Union[str, List[Union[TextContent, ImageContent]]]] = None
    reasoning_content: Optional[str] = Field(
        default=None,
        description="Model's reasoning/thinking process for models that support it (e.g., OpenAI o1, Anthropic Claude)"
    )
    name: Optional[str] = None
    tool_call_id: Optional[str] = None  # Required for tool messages
    tool_calls: Optional[list] = None  # For assistant messages
    attributes: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: Optional[EntitySource] = None  # Creator information (who created this message)
    platforms: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="References to where this message exists on external platforms. Maps platform name to platform-specific identifiers."
    )
    attachments: List[Attachment] = Field(default_factory=list)
    reactions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Map of emoji to list of user IDs who reacted with that emoji"
    )
    
    # Simple metrics structure
    metrics: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model": None,
            "timing": {
                "started_at": None,
                "ended_at": None,
                "latency": 0  # in milliseconds
            },
            "usage": {
                "completion_tokens": 0,
                "prompt_tokens": 0,
                "total_tokens": 0
            },
            "weave_call": {
                "id": "",
                "ui_url": ""
            }
        }
    )

    @field_validator("timestamp", mode="before")
    def ensure_timezone(cls, value: datetime) -> datetime:
        """Ensure timestamp is timezone-aware UTC"""
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @field_validator("role")
    def validate_role(cls, v):
        """Validate role field"""
        if v not in ["system", "user", "assistant", "tool"]:
            raise ValueError("Invalid role. Must be one of: system, user, assistant, tool")
        return v

    @model_validator(mode='after')
    def validate_tool_message(self):
        """Validate tool message requirements"""
        if self.role == "tool" and not self.tool_call_id:
            raise ValueError("tool_call_id is required for tool messages")
        return self

    @field_validator("tool_calls")
    def validate_tool_calls(cls, v, info):
        """Validate tool_calls field"""
        if v is not None:
            for tool_call in v:
                if not isinstance(tool_call, dict):
                    raise ValueError("Each tool call must be a dictionary")
                if "id" not in tool_call or "type" not in tool_call or "function" not in tool_call:
                    raise ValueError("Tool calls must have id, type, and function fields")
                if not isinstance(tool_call["function"], dict):
                    raise ValueError("Tool call function must be a dictionary")
                if "name" not in tool_call["function"] or "arguments" not in tool_call["function"]:
                    raise ValueError("Tool call function must have name and arguments fields")
        return v

    @field_validator("source")
    def validate_source(cls, v):
        """Validate source field structure"""
        if v is not None:
            # Check if type field is present and valid
            if "type" in v and v["type"] not in ["user", "agent", "tool"]:
                raise ValueError("source.type must be one of: user, agent, tool")
                
            # Ensure ID is present
            if "id" not in v:
                raise ValueError("source.id is required when source is present")
                
        return v

    def __init__(self, **data):
        # Handle file content if provided as raw bytes
        if "file_content" in data and "filename" in data:
            if "attachments" not in data:
                data["attachments"] = []
            data["attachments"].append(Attachment(
                filename=data.pop("filename"),
                content=data.pop("file_content")
            ))
        
        super().__init__(**data)
        if not self.id:
            # Create a hash of relevant properties
            hash_content = {
                "role": self.role,
                "sequence": self.sequence,  # Include sequence in hash
                "turn": self.turn,  # Include turn in hash
                "content": self.content,
                "timestamp": self.timestamp.isoformat()
            }
            # Include name for function messages
            if self.name and self.role == "tool":
                hash_content["name"] = self.name
                
            if self.source:
                hash_content["source"] = self.source
            
            # Create deterministic JSON string for hashing
            hash_str = json.dumps(hash_content, sort_keys=True)
            self.id = hashlib.sha256(hash_str.encode()).hexdigest()
            logger.debug(f"Generated message ID {self.id} from hash content: {hash_str}")

    def _serialize_tool_calls(self, tool_calls):
        """Helper method to serialize tool calls into a JSON-friendly format"""
        if not tool_calls:
            return None
            
        serialized_calls = []
        for call in tool_calls:
            try:
                # Handle OpenAI response objects
                if hasattr(call, 'model_dump'):
                    # For newer Pydantic models
                    call_dict = call.model_dump()
                elif hasattr(call, 'to_dict'):
                    # For objects with to_dict method
                    call_dict = call.to_dict()
                elif hasattr(call, 'id') and hasattr(call, 'function'):
                    # Direct access to OpenAI tool call attributes
                    call_dict = {
                        "id": call.id,
                        "type": getattr(call, 'type', 'function'),
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments
                        }
                    }
                elif isinstance(call, dict):
                    # If it's already a dict, ensure it has the required structure
                    call_dict = {
                        "id": call.get("id"),
                        "type": call.get("type", "function"),
                        "function": {
                            "name": call.get("function", {}).get("name"),
                            "arguments": call.get("function", {}).get("arguments")
                        }
                    }
                else:
                    logger.warning(f"Unsupported tool call format: {type(call)}")
                    continue

                # Validate the required fields are present
                if all(key in call_dict for key in ["id", "type", "function"]):
                    serialized_calls.append(call_dict)
                else:
                    logger.warning(f"Missing required fields in tool call: {call_dict}")
            except Exception as e:
                logger.error(f"Error serializing tool call: {str(e)}")
                continue
                
        return serialized_calls

    def model_dump(self, mode: str = "json") -> Dict[str, Any]:
        """Convert message to a dictionary suitable for JSON serialization
        
        Args:
            mode: Serialization mode, either "json" or "python". 
                 "json" converts datetimes to ISO strings (default).
                 "python" keeps datetimes as datetime objects.
        """
        message_dict = {
            "id": self.id,
            "role": self.role,
            "sequence": self.sequence,  # Include sequence in serialization
            "turn": self.turn,  # Include turn in serialization
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if mode == "json" else self.timestamp,
            "source": self.source,
            "platforms": self.platforms,
            "metrics": self.metrics,
            "reactions": self.reactions
        }
        
        if self.reasoning_content:
            message_dict["reasoning_content"] = self.reasoning_content
        
        if self.name:
            message_dict["name"] = self.name
            
        if self.tool_call_id:
            message_dict["tool_call_id"] = self.tool_call_id
            
        if self.tool_calls:
            message_dict["tool_calls"] = self._serialize_tool_calls(self.tool_calls)
            
        if self.attributes:
            message_dict["attributes"] = self.attributes

        if self.attachments:
            message_dict["attachments"] = []
            for attachment in self.attachments:
                # Ensure content is properly serialized
                attachment_dict = attachment.model_dump(mode=mode) if hasattr(attachment, 'model_dump') else {
                    "filename": attachment.filename,
                    "mime_type": attachment.mime_type,
                    "file_id": attachment.file_id,
                    "storage_path": attachment.storage_path,
                    "storage_backend": attachment.storage_backend,
                    "status": attachment.status
                }
                
                # Remove content field if present to avoid large data serialization
                if "content" in attachment_dict:
                    del attachment_dict["content"]
                
                # Add processed content if available
                if attachment.attributes:
                    attachment_dict["attributes"] = attachment.attributes
                
                # Add to attachments list
                message_dict["attachments"].append(attachment_dict)
            
        return message_dict
        
    def to_chat_completion_message(self, file_store: Optional[FileStore] = None) -> Dict[str, Any]:
        """Return message in the format expected by chat completion APIs
        
        Args:
            file_store: Optional FileStore instance for accessing file URLs
        """
        base_content = self.content if isinstance(self.content, str) else ""
        
        message_dict = {
            "role": self.role,
            "content": base_content,
            "sequence": self.sequence
        }
        
        if self.name:
            message_dict["name"] = self.name
            
        if self.role == "assistant" and self.tool_calls:
            message_dict["tool_calls"] = self.tool_calls
            
        if self.role == "tool" and self.tool_call_id:
            message_dict["tool_call_id"] = self.tool_call_id

        # Handle attachments if we have them
        if self.attachments:
            # Get file references for all attachments
            file_references = []
            for attachment in self.attachments:
                if not attachment.storage_path:
                    continue
                
                # Get the URL from attributes if available, otherwise construct it
                file_url = attachment.attributes.get("url") if attachment.attributes else None
                
                if not file_url and attachment.storage_path:
                    # Construct URL from storage path
                    file_url = FileStore.get_file_url(attachment.storage_path)
                
                # Simplified file reference format
                file_ref = f"[File: {file_url} ({attachment.mime_type})]"
                file_references.append(file_ref)
            
            # Add file references to content based on message role
            if file_references:
                if self.role == "user" or self.role == "tool":
                    # For user and tool messages, add file references directly
                    if message_dict["content"]:
                        message_dict["content"] += "\n\n" + "\n".join(file_references)
                    else:
                        message_dict["content"] = "\n".join(file_references)
                elif self.role == "assistant":
                    # For assistant messages, add a header
                    if message_dict["content"]:
                        message_dict["content"] += "\n\nGenerated Files:\n" + "\n".join(file_references)
                    else:
                        message_dict["content"] = "Generated Files:\n" + "\n".join(file_references)
        
        return message_dict

    def add_attachment(self, attachment: Union[Attachment, bytes], filename: Optional[str] = None) -> None:
        """Add an attachment to the message.
        
        Args:
            attachment: Either an Attachment object or raw bytes
            filename: Required if attachment is bytes, ignored if attachment is Attachment
        
        Raises:
            ValueError: If attachment is bytes and filename is not provided
        """
        if isinstance(attachment, Attachment):
            self.attachments.append(attachment)
        elif isinstance(attachment, bytes):
            if not filename:
                raise ValueError("filename is required when adding raw bytes as attachment")
            att = Attachment(
                filename=filename,
                content=attachment
            )
            self.attachments.append(att)
        else:
            raise ValueError("attachment must be either Attachment object or bytes")

    def add_reaction(self, emoji: str, user_id: str) -> bool:
        """Add a reaction to a message.
        
        Args:
            emoji: Emoji shortcode (e.g., ":thumbsup:")
            user_id: ID of the user adding the reaction
            
        Returns:
            True if reaction was added, False if it already existed
        """
        logger.info(f"Message.add_reaction (msg_id={self.id}): Current reactions: {self.reactions}. Adding '{emoji}' for user '{user_id}'.")
        if emoji not in self.reactions:
            self.reactions[emoji] = []
        
        if user_id in self.reactions[emoji]:
            logger.warning(f"Message.add_reaction (msg_id={self.id}): User '{user_id}' already reacted with '{emoji}'.")
            return False # Indicate that reaction was not newly added because it already existed
        
        self.reactions[emoji].append(user_id)
        logger.info(f"Message.add_reaction (msg_id={self.id}): Successfully added. Reactions now: {self.reactions}")
        return True

    def remove_reaction(self, emoji: str, user_id: str) -> bool:
        """Remove a reaction from a message.
        
        Args:
            emoji: Emoji shortcode (e.g., ":thumbsup:")
            user_id: ID of the user removing the reaction
            
        Returns:
            True if reaction was removed, False if it didn't exist
        """
        logger.info(f"Message.remove_reaction (msg_id={self.id}): Current reactions: {self.reactions}. Removing '{emoji}' for user '{user_id}'.")
        if emoji not in self.reactions or user_id not in self.reactions[emoji]:
            logger.warning(f"Message.remove_reaction (msg_id={self.id}): Emoji '{emoji}' or user '{user_id}' not found in reactions {self.reactions}.")
            return False
        
        self.reactions[emoji].remove(user_id)
        
        # Clean up empty reactions
        if not self.reactions[emoji]:
            del self.reactions[emoji]
            
        logger.info(f"Message.remove_reaction (msg_id={self.id}): Successfully removed. Reactions now: {self.reactions}")
        return True

    def get_reactions(self) -> Dict[str, List[str]]:
        """Get all reactions for this message.
        
        Returns:
            Dictionary mapping emoji to list of user IDs
        """
        return self.reactions

    def get_reaction_counts(self) -> Dict[str, int]:
        """Get counts of reactions for this message.
        
        Returns:
            Dictionary mapping emoji to count of reactions
        """
        return {emoji: len(users) for emoji, users in self.reactions.items()}

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "role": "user",
                    "sequence": 1,
                    "turn": 1,
                    "content": "Here are some files to look at",
                    "name": None,
                    "tool_call_id": None,
                    "tool_calls": None,
                    "attributes": {},
                    "timestamp": "2024-02-07T00:00:00+00:00",
                    "source": {
                        "entity": {
                            "id": "U123456",
                            "name": "John Doe",
                            "type": "user",
                            "attributes": {
                                "email": "john.doe@example.com",
                                "user_id": "U123456"
                            }
                        },
                        "platform": {
                            "name": "slack",
                            "attributes": {
                                "thread_ts": "1234567890.123456",
                                "channel_id": "C123456",
                                "team_id": "T123456"
                            }
                        }
                    },
                    "attachments": [
                        {
                            "filename": "example.txt",
                            "mime_type": "text/plain",
                            "attributes": {
                                "type": "text",
                                "text": "Example content",
                                "url": "/files/example.txt"
                            },
                            "status": "stored"
                        },
                        {
                            "filename": "example.pdf",
                            "mime_type": "application/pdf",
                            "attributes": {
                                "type": "document",
                                "text": "Extracted text from PDF",
                                "url": "/files/example.pdf"
                            },
                            "status": "stored"
                        },
                        {
                            "filename": "example.jpg",
                            "mime_type": "image/jpeg",
                            "attributes": {
                                "type": "image",
                                "url": "/files/example.jpg"
                            },
                            "status": "stored"
                        }
                    ],
                    "metrics": {
                        "model": "gpt-4.1",
                        "timing": {
                            "started_at": "2024-02-07T00:00:00+00:00",
                            "ended_at": "2024-02-07T00:00:01+00:00",
                            "latency": 1.0
                        },
                        "usage": {
                            "completion_tokens": 100,
                            "prompt_tokens": 50,
                            "total_tokens": 150
                        },
                        "weave_call": {
                            "id": "call-123",
                            "ui_url": "https://weave.ui/call-123"
                        }
                    },
                    "reactions": {
                        ":thumbsup:": ["U123456", "U234567"],
                        ":heart:": ["U123456"]
                    }
                }
            ]
        },
        "extra": "forbid",
        "validate_assignment": True
    } 