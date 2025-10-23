from enum import Enum
from typing import Any, Dict, Optional

from pydantic import Field, model_validator

from gslides_api.domain.domain import GSlidesBaseModel


class RangeType(Enum):
    """Enumeration of possible range types for text selection."""

    ALL = "ALL"
    """Selects all the text in the target shape or table cell."""

    FIXED_RANGE = "FIXED_RANGE"
    """Selects a specific range of text using start and end indexes."""

    FROM_START_INDEX = "FROM_START_INDEX"
    """Selects text from a start index to the end of the text."""


class ApplyMode(Enum):
    """Enumeration of possible apply modes for replace all text requests."""

    APPLY_MODE_UNSPECIFIED = "APPLY_MODE_UNSPECIFIED"  # Unspecified mode.
    RELATIVE = "RELATIVE"  # Applies the new AffineTransform matrix to the existing one, and replaces the existing one with the resulting concatenation.
    ABSOLUTE = (
        "ABSOLUTE"  # Replaces the existing AffineTransform matrix with the new one.
    )


class Range(GSlidesBaseModel):
    """Represents a range of text within a shape or table cell.

    The range can be specified in different ways:
    - ALL: Select all text
    - FIXED_RANGE: Select text between startIndex and endIndex
    - FROM_START_INDEX: Select text from startIndex to the end
    """

    type: RangeType = Field(description="The type of range selection")
    startIndex: Optional[int] = Field(
        default=None, description="The starting index of the range (0-based)"
    )
    endIndex: Optional[int] = Field(
        default=None, description="The ending index of the range (exclusive)"
    )

    @model_validator(mode="after")
    def validate_range_consistency(self) -> "Range":
        """Validate that the range parameters are consistent with the type."""
        if self.type == RangeType.ALL:
            if self.startIndex is not None or self.endIndex is not None:
                raise ValueError(
                    "startIndex and endIndex must be None when type is ALL"
                )
        elif self.type == RangeType.FIXED_RANGE:
            if self.startIndex is None or self.endIndex is None:
                raise ValueError(
                    "Both startIndex and endIndex must be provided when type is FIXED_RANGE"
                )
            if self.startIndex >= self.endIndex:
                raise ValueError("startIndex must be less than endIndex")
        elif self.type == RangeType.FROM_START_INDEX:
            if self.startIndex is None:
                raise ValueError(
                    "startIndex must be provided when type is FROM_START_INDEX"
                )
            if self.endIndex is not None:
                raise ValueError("endIndex must be None when type is FROM_START_INDEX")
        return self


class PlaceholderIdMapping(GSlidesBaseModel):
    """Represents a mapping of placeholder IDs for slide creation."""

    layoutPlaceholder: Dict[str, Any] = Field(
        description="The placeholder on the layout"
    )
    layoutPlaceholderObjectId: str = Field(
        description="The object ID of the layout placeholder"
    )
    objectId: str = Field(description="The object ID to assign to the placeholder")


class ObjectIdMapping(GSlidesBaseModel):
    """Represents a mapping of object IDs for duplication operations."""

    objectIds: Dict[str, str] = Field(
        description="A map of object IDs to their new IDs"
    )


class SubstringMatchCriteria(GSlidesBaseModel):
    """Represents a criteria that can be used to match a substring within a text.

    https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations/request#SubstringMatchCriteria
    """

    text: Optional[str] = None
    matchCase: Optional[bool] = None
    searchByRegex: Optional[bool] = None
