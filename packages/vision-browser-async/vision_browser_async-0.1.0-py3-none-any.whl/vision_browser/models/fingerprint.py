from ..base import BaseModel


class Screen(BaseModel):
    width: int
    height: int
    pixel_ratio: float
    avail_width: int
    avail_height: int
    avail_top: int
    avail_left: int
    color_depth: int
    pixel_depth: int


class Hints(BaseModel):
    architecture: str
    bitness: int
    model: str
    platform: str
    platform_version: str
    ua_full_version: str
    mobile: bool


class Navigator(BaseModel):
    hardware_concurrency: int
    device_memory: float
    max_touch_points: int
    user_agent: str
    platform: str
    language: str
    languages: list[str]
    quota: int | None


class WebGL(BaseModel):
    unmasked_renderer: str
    unmasked_vendor: str
    extensions: list[str]
    extensions_v2: list[str]
    extra: dict[str, int | float | None]


class WebGPU(BaseModel):
    vendor: str
    architecture: str
    limits: dict[str, int | float | None]


class Fingerprint(BaseModel):
    major: int
    os: str
    screen: Screen
    fonts: list[str]
    hints: Hints
    navigator: Navigator
    webgl: WebGL
    webgpu: WebGPU
    crc: str
