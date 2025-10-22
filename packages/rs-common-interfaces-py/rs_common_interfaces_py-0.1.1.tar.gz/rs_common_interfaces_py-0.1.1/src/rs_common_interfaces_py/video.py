from enum import Enum
from typing import Optional, List, Literal, Union
import re

from dataclasses import dataclass, field

from rs_common_interfaces_py.request import RsRequest


def text_contains(text: str, contains: str) -> bool:
    formatted = f".{contains}."
    return formatted in text or text.startswith(contains) or text.endswith(contains)


class RsVideoFormat(str, Enum):
    MP4 = "mp4"
    M4V = "m4v"
    MOV = "mov"
    MKV = "mkv"
    WEBM = "webm"
    WMV = "wmv"
    AVI = "avi"
    OTHER = "other"

    def to_extension(self) -> str:
        if self == RsVideoFormat.OTHER:
            return ""
        return f".{self.value}"

    @classmethod
    def from_filename(cls, filename: str) -> 'RsVideoFormat':
        filename_lower = filename.lower()
        if filename_lower.endswith(".mkv"):
            return cls.MKV
        elif filename_lower.endswith(".mp4"):
            return cls.MP4
        elif filename_lower.endswith(".m4v"):
            return cls.M4V
        elif filename_lower.endswith(".mov"):
            return cls.MOV
        elif filename_lower.endswith(".webm"):
            return cls.WEBM
        elif filename_lower.endswith(".wmv"):
            return cls.WMV
        elif filename_lower.endswith(".avi"):
            return cls.AVI
        else:
            return cls.OTHER

    def as_mime(self) -> str:
        mapping = {
            RsVideoFormat.MP4: "video/mp4",
            RsVideoFormat.M4V: "video/x-m4v",
            RsVideoFormat.MOV: "video/quicktime",
            RsVideoFormat.MKV: "application/x-matroska",
            RsVideoFormat.WEBM: "video/webm",
            RsVideoFormat.WMV: "video/x-ms-wmv",
            RsVideoFormat.AVI: "video/x-msvideo",
            RsVideoFormat.OTHER: "application/octet-stream",
        }
        return mapping[self]

    @classmethod
    def from_mime(cls, mime: str) -> Optional['RsVideoFormat']:
        inverse_mapping = {
            "video/mp4": cls.MP4,
            "video/x-m4v": cls.M4V,
            "video/quicktime": cls.MOV,
            "application/x-matroska": cls.MKV,
            "video/webm": cls.WEBM,
            "video/x-ms-wmv": cls.WMV,
            "video/x-msvideo": cls.AVI,
            "application/octet-stream": cls.OTHER,
        }
        return inverse_mapping.get(mime)


class RsResolution(str, Enum):
    UHD = "4K"
    FULL_HD = "1080p"
    HD = "720p"
    # Note: Custom(String) variant omitted; handle as str for custom resolutions
    # e.g., resolution: Optional[Union[RsResolution, str]] in models
    UNKNOWN = "unknown"

    @classmethod
    def default(cls) -> 'RsResolution':
        return cls.UNKNOWN

    @classmethod
    def from_filename(cls, filename: str) -> 'RsResolution':
        modified_filename = re.sub(r'[ \-_\s]', '.', filename.lower())
        if text_contains(modified_filename, "1080p"):
            return cls.FULL_HD
        elif text_contains(modified_filename, "720p"):
            return cls.HD
        elif text_contains(modified_filename, "4k") or text_contains(modified_filename, "2160p"):
            return cls.UHD
        else:
            return cls.UNKNOWN


class RsVideoCodec(str, Enum):
    H265 = "h265"
    H264 = "h264"
    AV1 = "av1"
    XVID = "xvid"
    # Note: Custom(String) variant omitted; handle as str for custom codecs
    UNKNOWN = "unknown"

    @classmethod
    def default(cls) -> 'RsVideoCodec':
        return cls.UNKNOWN

    @classmethod
    def from_filename(cls, filename: str) -> 'RsVideoCodec':
        modified_filename = re.sub(r'[ \-_\s]', '.', filename.lower())
        if (text_contains(modified_filename, "x265") or
            text_contains(modified_filename, "x.265") or
            text_contains(modified_filename, "hevc") or
            text_contains(modified_filename, "h265") or
            text_contains(modified_filename, "h.265")):
            return cls.H265
        elif (text_contains(modified_filename, "h264") or
              text_contains(modified_filename, "h.264") or
              text_contains(modified_filename, "x.264") or
              text_contains(modified_filename, "x264")):
            return cls.H264
        elif text_contains(modified_filename, "av1"):
            return cls.AV1
        elif text_contains(modified_filename, "xvid"):
            return cls.XVID
        else:
            return cls.UNKNOWN


class RsAudio(str, Enum):
    ATMOS = "Atmos"
    DDP51 = "DDP5.1"
    DTSHD = "DTSHD"
    DTSX = "DTSX"
    DTS = "DTS"
    AC351 = "AC35.1"
    AAC51 = "AAC5.1"
    AAC = "AAC"
    MP3 = "MP3"
    # Note: Custom(String) variant omitted; handle as str for custom audio
    UNKNOWN = "unknown"

    @classmethod
    def default(cls) -> 'RsAudio':
        return cls.UNKNOWN

    @classmethod
    def from_filename(cls, filename: str) -> 'RsAudio':
        modified_filename = re.sub(r'[ \-_\s]', '.', filename.lower())
        if text_contains(modified_filename, "atmos"):
            return cls.ATMOS
        elif (text_contains(modified_filename, "ddp5.1") or
              text_contains(modified_filename, "ddp51") or
              text_contains(modified_filename, "dolby.digital.plus.5.1") or
              text_contains(modified_filename, "dd51")):
            return cls.DDP51
        elif text_contains(modified_filename, "dtshd"):
            return cls.DTSHD
        elif text_contains(modified_filename, "dtsx"):
            return cls.DTSX
        elif text_contains(modified_filename, "dts"):
            return cls.DTS
        elif text_contains(modified_filename, "ac35.1") or text_contains(modified_filename, "ac3.5.1"):
            return cls.AC351
        elif text_contains(modified_filename, "aac5.1") or text_contains(modified_filename, "aac51"):
            return cls.AAC51
        elif text_contains(modified_filename, "aac"):
            return cls.AAC
        elif text_contains(modified_filename, "mp3"):
            return cls.MP3
        else:
            return cls.UNKNOWN

    @classmethod
    def list_from_filename(cls, filename: str) -> List['RsAudio']:
        result = []
        modified_filename = re.sub(r'[ \-_\s]', '.', filename.lower())
        if text_contains(modified_filename, "atmos"):
            result.append(cls.ATMOS)
        if text_contains(modified_filename, "ddp5.1"):
            result.append(cls.DDP51)
        if text_contains(modified_filename, "dtshd"):
            result.append(cls.DTSHD)
        if text_contains(modified_filename, "dtsx"):
            result.append(cls.DTSX)
        if text_contains(modified_filename, "dts"):
            result.append(cls.DTS)
        if text_contains(modified_filename, "ac35.1") or text_contains(modified_filename, "ac3.5.1"):
            result.append(cls.AC351)
        # Note: list_from_filename in Rust appears truncated; added only matching conditions from snippet
        return result
    

    
class VideoOverlayPosition(Enum):
    TOP_LEFT = "topLeft"
    TOP_RIGHT = "topRight"
    BOTTOM_LEFT = "bottomLeft"
    BOTTOM_RIGHT = "bottomRight"
    BOTTOM_CENTER = "bottomCenter"
    TOP_CENTER = "topCenter"
    CENTER = "center"

    @classmethod
    def default(cls):
        return cls.TOP_RIGHT

    def as_filter(self, margin: float) -> str:
        if self == VideoOverlayPosition.TOP_LEFT:
            return f"main_w*{margin}:main_h*{margin}"
        elif self == VideoOverlayPosition.TOP_RIGHT:
            return f"(main_w-w):min(main_h,main_w)*{margin}"
        elif self == VideoOverlayPosition.BOTTOM_LEFT:
            return f"main_w*{margin}:(main_h-h)"
        elif self == VideoOverlayPosition.BOTTOM_RIGHT:
            return "(main_w-w):(main_h-h)"
        elif self == VideoOverlayPosition.BOTTOM_CENTER:
            return f"main_w*0.5:(main_h-h)"  # TODO: Adjust if needed
        elif self == VideoOverlayPosition.TOP_CENTER:
            return f"(main_w-w)/2:main_h*{margin}"  # TODO: Adjust if needed
        elif self == VideoOverlayPosition.CENTER:
            return f"(main_w-w)/2:(main_h-h)/2"  # TODO: Adjust if needed
        raise ValueError(f"Unknown position: {self}")

    def as_ass_alignment(self) -> str:
        if self == VideoOverlayPosition.TOP_LEFT:
            return "7"
        elif self == VideoOverlayPosition.TOP_CENTER:
            return "8"
        elif self == VideoOverlayPosition.TOP_RIGHT:
            return "9"
        elif self == VideoOverlayPosition.CENTER:
            return "5"
        elif self == VideoOverlayPosition.BOTTOM_LEFT:
            return "1"
        elif self == VideoOverlayPosition.BOTTOM_CENTER:
            return "2"
        elif self == VideoOverlayPosition.BOTTOM_RIGHT:
            return "3"
        raise ValueError(f"Unknown position: {self}")


class VideoAlignment(Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"

    @classmethod
    def default(cls):
        return cls.CENTER


class VideoOverlayType(Enum):
    WATERMARK = "watermark"
    FILE = "file"


@dataclass
class VideoConvertInterval:
    start: float
    duration: Optional[float] = None
    # will default to current input
    input: Optional[str] = None


@dataclass
class VideoOverlay:
    kind: VideoOverlayType
    path: str
    ratio: float
    opacity: float
    position: VideoOverlayPosition = field(default_factory=VideoOverlayPosition.default)
    margin: Optional[float] = None


@dataclass
class VideoTextOverlay:
    text: str
    font_size: int
    font_color: Optional[str] = None
    font: Optional[str] = None
    position: VideoOverlayPosition = field(default_factory=VideoOverlayPosition.default)
    margin_vertical: Optional[int] = None
    margin_horizontal: Optional[int] = None
    margin_right: Optional[int] = None
    margin_bottom: Optional[int] = None
    opacity: Optional[float] = None
    shadow_color: Optional[str] = None
    shado_opacity: Optional[float] = None  # Note: Matches Rust typo
    start: Optional[int] = None
    end: Optional[int] = None




