"""Common interface types for video processing and request handling."""

# Import from request module
from .request import (
    RsRequestStatus,
    RsRequestFiles,
    RsCookie,
    RsRequest,
    header_value,
    headers,
)

# Import from video module
from .video import (
    RsVideoFormat,
    RsResolution,
    RsVideoCodec,
    RsAudio,
    VideoOverlayPosition,
    VideoAlignment,
    VideoOverlayType,
    VideoConvertInterval,
    VideoOverlay,
    VideoTextOverlay,
    VideoConvertRequest,
    VideoConvertJob,
)

__all__ = [
    # Request types
    "RsRequestStatus",
    "RsRequestFiles",
    "RsCookie",
    "RsRequest",
    "header_value",
    "headers",
    # Video types
    "RsVideoFormat",
    "RsResolution",
    "RsVideoCodec",
    "RsAudio",
    "VideoOverlayPosition",
    "VideoAlignment",
    "VideoOverlayType",
    "VideoConvertInterval",
    "VideoOverlay",
    "VideoTextOverlay",
    "VideoConvertRequest",
    "VideoConvertJob",
]

__version__ = "0.1.0"