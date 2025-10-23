# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._utils import PropertyInfo

__all__ = [
    "CharacterPerformanceCreateParams",
    "Character",
    "CharacterImage",
    "CharacterVideo",
    "Reference",
    "ContentModeration",
]


class CharacterPerformanceCreateParams(TypedDict, total=False):
    character: Required[Character]
    """The character to control.

    You can either provide a video or an image. A visually recognizable face must be
    visible and stay within the frame.
    """

    model: Required[Literal["act_two"]]

    reference: Required[Reference]
    """The reference video containing the performance to apply to the character."""

    body_control: Annotated[bool, PropertyInfo(alias="bodyControl")]
    """A boolean indicating whether to enable body control.

    When enabled, non-facial movements and gestures will be applied to the character
    in addition to facial expressions.
    """

    content_moderation: Annotated[ContentModeration, PropertyInfo(alias="contentModeration")]
    """Settings that affect the behavior of the content moderation system."""

    expression_intensity: Annotated[int, PropertyInfo(alias="expressionIntensity")]
    """An integer between 1 and 5 (inclusive).

    A larger value increases the intensity of the character's expression.
    """

    ratio: Literal["1280:720", "720:1280", "960:960", "1104:832", "832:1104", "1584:672"]
    """The resolution of the output video."""

    seed: int


class CharacterImage(TypedDict, total=False):
    type: Required[Literal["image"]]

    uri: Required[str]
    """A data URI containing an encoded image."""


class CharacterVideo(TypedDict, total=False):
    type: Required[Literal["video"]]

    uri: Required[str]
    """A data URI containing an encoded video."""


Character: TypeAlias = Union[CharacterImage, CharacterVideo]


class Reference(TypedDict, total=False):
    type: Required[Literal["video"]]

    uri: Required[str]
    """A data URI containing an encoded video."""


class ContentModeration(TypedDict, total=False):
    public_figure_threshold: Annotated[Literal["auto", "low"], PropertyInfo(alias="publicFigureThreshold")]
