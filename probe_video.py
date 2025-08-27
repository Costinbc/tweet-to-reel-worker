import json, subprocess, os
from typing import TypedDict


class VideoProbe(TypedDict, total=False):
    path: str
    size_bytes: int
    width: int
    height: int
    duration: float
    fps: float
    codec: str
    pix_fmt: str
    aspect: float


def _parse_fps(s: str) -> float:
    if not s: return 0.0
    if "/" in s:
        n, d = s.split("/")
        return float(n) / float(d) if float(d) != 0 else float(n)
    return float(s)


def probe_video(path: str) -> VideoProbe:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,codec_name,pix_fmt",
        "-show_entries", "format=duration,size",
        "-of", "json", path,
    ]
    out = subprocess.check_output(cmd, text=True)
    data = json.loads(out)

    st = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}

    width = int(st.get("width") or 0)
    height = int(st.get("height") or 0)
    duration = float(fmt.get("duration") or 0.0)
    fps = _parse_fps(st.get("avg_frame_rate") or "0/1")
    pix_fmt = st.get("pix_fmt") or ""
    codec = st.get("codec_name") or ""
    size_bytes = int(fmt.get("size") or 0)

    return VideoProbe(
        path=path,
        size_bytes=size_bytes,
        width=width,
        height=height,
        duration=duration,
        fps=fps,
        codec=codec,
        pix_fmt=pix_fmt,
        aspect=(height / width) if width and height else 0.0
    )
