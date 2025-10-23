# File: src/noveler/application/schemas.py
# Purpose: Command and event schema definitions with validation
# Context: Pydantic-based validation for MessageBus inputs and outputs

"""Pydantic schemas for MessageBus command and event validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class CommandType(str, Enum):
    """Standard command types."""
    CREATE_EPISODE = "create_episode"
    UPDATE_EPISODE = "update_episode"
    CHECK_QUALITY = "check_quality"
    PUBLISH_EPISODE = "publish_episode"
    UPDATE_PLOT = "update_plot"
    GENERATE_PLOT = "generate_plot"


class EventType(str, Enum):
    """Standard event types with namespaces."""
    # Episode events
    EPISODE_CREATED = "episode.created"
    EPISODE_UPDATED = "episode.updated"
    EPISODE_PUBLISHED = "episode.published"

    # Quality events
    QUALITY_CHECKED = "quality.checked"
    QUALITY_IMPROVED = "quality.improved"
    QUALITY_FAILED = "quality.failed"

    # Plot events
    PLOT_GENERATED = "plot.generated"
    PLOT_UPDATED = "plot.updated"
    PLOT_VALIDATED = "plot.validated"


# Base schemas
class BaseCommand(BaseModel):
    """Base command schema with common fields."""

    command_id: Optional[str] = Field(None, description="Unique command identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Command timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        extra = "forbid"  # Strict validation


class BaseEvent(BaseModel):
    """Base event schema with common fields."""

    event_id: Optional[str] = Field(None, description="Unique event identifier")
    event_type: str = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")

    class Config:
        extra = "forbid"


# Command schemas
class CreateEpisodeCommand(BaseCommand):
    """Command to create a new episode."""

    title: str = Field(..., min_length=1, max_length=200, description="Episode title")
    episode_number: int = Field(..., ge=1, description="Episode number")
    content: str = Field(default="", description="Episode content")

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()


class UpdateEpisodeCommand(BaseCommand):
    """Command to update an existing episode."""

    episode_id: str = Field(..., min_length=1, description="Episode ID")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="New title")
    content: Optional[str] = Field(None, description="New content")

    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip() if v else v


class CheckQualityCommand(BaseCommand):
    """Command to check content quality."""

    content: str = Field(..., min_length=1, description="Content to check")
    check_types: list[str] = Field(default_factory=lambda: ["grammar", "readability"], description="Quality check types")
    target_score: float = Field(default=80.0, ge=0.0, le=100.0, description="Target quality score")

    @validator('check_types')
    def validate_check_types(cls, v):
        valid_types = {"grammar", "readability", "rhythm", "content", "dialogue"}
        invalid = set(v) - valid_types
        if invalid:
            raise ValueError(f'Invalid check types: {invalid}. Valid types: {valid_types}')
        return v


class PublishEpisodeCommand(BaseCommand):
    """Command to publish an episode."""

    episode_id: str = Field(..., min_length=1, description="Episode ID")
    format_type: str = Field(default="html", description="Publication format")
    include_metadata: bool = Field(default=True, description="Include metadata in publication")


class UpdatePlotCommand(BaseCommand):
    """Command to update plot information."""

    plot_id: str = Field(..., min_length=1, description="Plot ID")
    episode_number: Optional[int] = Field(None, ge=1, description="Episode number")
    plot_content: str = Field(..., min_length=1, description="Plot content")
    consistency_check: bool = Field(default=True, description="Run consistency check")


class GeneratePlotCommand(BaseCommand):
    """Command to generate new plot."""

    episode_number: int = Field(..., ge=1, description="Episode number")
    chapter_title: Optional[str] = Field(None, description="Chapter title")
    target_length: Optional[int] = Field(None, ge=100, description="Target word count")
    genre: Optional[str] = Field(None, description="Genre preference")
    use_ai_enhancement: bool = Field(default=True, description="Use AI enhancement")


# Event schemas
class EpisodeCreatedEvent(BaseEvent):
    """Event fired when an episode is created."""

    event_type: str = Field(default=EventType.EPISODE_CREATED, const=True)
    episode_id: str = Field(..., description="Created episode ID")
    title: str = Field(..., description="Episode title")
    episode_number: int = Field(..., description="Episode number")


class EpisodeUpdatedEvent(BaseEvent):
    """Event fired when an episode is updated."""

    event_type: str = Field(default=EventType.EPISODE_UPDATED, const=True)
    episode_id: str = Field(..., description="Updated episode ID")
    changes: Dict[str, Any] = Field(..., description="Changed fields")


class QualityCheckedEvent(BaseEvent):
    """Event fired when quality check is completed."""

    event_type: str = Field(default=EventType.QUALITY_CHECKED, const=True)
    content_id: str = Field(..., description="Content ID")
    score: float = Field(..., ge=0.0, le=100.0, description="Quality score")
    check_types: list[str] = Field(..., description="Types of checks performed")
    passed: bool = Field(..., description="Whether quality check passed")
    issues: list[Dict[str, Any]] = Field(default_factory=list, description="Quality issues found")


class PlotGeneratedEvent(BaseEvent):
    """Event fired when plot is generated."""

    event_type: str = Field(default=EventType.PLOT_GENERATED, const=True)
    plot_id: str = Field(..., description="Generated plot ID")
    episode_number: int = Field(..., description="Episode number")
    word_count: int = Field(..., description="Generated plot word count")
    ai_enhanced: bool = Field(..., description="Whether AI enhancement was used")


# Schema registry
COMMAND_SCHEMAS: Dict[str, type[BaseCommand]] = {
    CommandType.CREATE_EPISODE: CreateEpisodeCommand,
    CommandType.UPDATE_EPISODE: UpdateEpisodeCommand,
    CommandType.CHECK_QUALITY: CheckQualityCommand,
    CommandType.PUBLISH_EPISODE: PublishEpisodeCommand,
    CommandType.UPDATE_PLOT: UpdatePlotCommand,
    CommandType.GENERATE_PLOT: GeneratePlotCommand,
}

EVENT_SCHEMAS: Dict[str, type[BaseEvent]] = {
    EventType.EPISODE_CREATED: EpisodeCreatedEvent,
    EventType.EPISODE_UPDATED: EpisodeUpdatedEvent,
    EventType.QUALITY_CHECKED: QualityCheckedEvent,
    EventType.PLOT_GENERATED: PlotGeneratedEvent,
}


def validate_command(command_name: str, data: Dict[str, Any]) -> BaseCommand:
    """Validate command data against schema.

    Args:
        command_name: Command type name
        data: Command data to validate

    Returns:
        Validated command instance

    Raises:
        ValueError: If validation fails
        KeyError: If command schema not found
    """
    if command_name not in COMMAND_SCHEMAS:
        raise KeyError(f"Unknown command type: {command_name}")

    schema_class = COMMAND_SCHEMAS[command_name]
    try:
        return schema_class(**data)
    except Exception as e:
        raise ValueError(f"Command validation failed for {command_name}: {e}") from e


def validate_event(event_type: str, data: Dict[str, Any]) -> BaseEvent:
    """Validate event data against schema.

    Args:
        event_type: Event type name
        data: Event data to validate

    Returns:
        Validated event instance

    Raises:
        ValueError: If validation fails
        KeyError: If event schema not found
    """
    if event_type not in EVENT_SCHEMAS:
        # For unknown event types, use base schema
        return BaseEvent(event_type=event_type, **data)

    schema_class = EVENT_SCHEMAS[event_type]
    try:
        return schema_class(**data)
    except Exception as e:
        raise ValueError(f"Event validation failed for {event_type}: {e}") from e


def get_command_schema(command_name: str) -> type[BaseCommand]:
    """Get command schema class.

    Args:
        command_name: Command type name

    Returns:
        Command schema class

    Raises:
        KeyError: If command schema not found
    """
    if command_name not in COMMAND_SCHEMAS:
        raise KeyError(f"Unknown command type: {command_name}")
    return COMMAND_SCHEMAS[command_name]


def get_event_schema(event_type: str) -> type[BaseEvent]:
    """Get event schema class.

    Args:
        event_type: Event type name

    Returns:
        Event schema class (BaseEvent if not found)
    """
    return EVENT_SCHEMAS.get(event_type, BaseEvent)


def list_available_commands() -> list[str]:
    """Get list of available command types."""
    return list(COMMAND_SCHEMAS.keys())


def list_available_events() -> list[str]:
    """Get list of available event types."""
    return list(EVENT_SCHEMAS.keys())
