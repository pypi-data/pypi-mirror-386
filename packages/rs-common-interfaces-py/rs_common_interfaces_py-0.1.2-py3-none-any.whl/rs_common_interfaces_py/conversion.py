
from dataclasses import dataclass, field
from typing import List, Optional

from .request import RsRequest
from .video import (
    RsVideoFormat,
    RsVideoCodec,
    VideoAlignment,
    VideoOverlay,
    VideoTextOverlay,
    VideoConvertInterval
)




@dataclass
class VideoConvertRequest:
    id: str
    format: RsVideoFormat  # Assuming RsVideoFormat is a string or enum; adjust as needed
    codec: Optional[RsVideoCodec] = None  # Assuming RsVideoCodec is a string or enum; adjust as needed
    crf: Optional[int] = None
    no_audio: bool = False
    width: Optional[str] = None
    height: Optional[str] = None
    framerate: Optional[int] = None
    crop_width: Optional[int] = None
    crop_height: Optional[int] = None
    aspect_ratio: Optional[str] = None
    aspect_ratio_alignment: Optional[VideoAlignment] = None
    overlay: Optional[VideoOverlay] = None
    texts: Optional[List[VideoTextOverlay]] = None
    intervals: List[VideoConvertInterval] = field(default_factory=list)

@dataclass
class VideoConvertJob:
    request: VideoConvertRequest
    source: RsRequest


