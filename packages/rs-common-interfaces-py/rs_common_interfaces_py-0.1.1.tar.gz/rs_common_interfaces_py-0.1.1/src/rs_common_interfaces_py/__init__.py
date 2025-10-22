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
    
)

from .conversion import (VideoConvertJob, VideoConvertRequest)

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
    # Convert types
    "VideoConvertRequest",
    "VideoConvertJob",
]

__version__ = "0.1.1"