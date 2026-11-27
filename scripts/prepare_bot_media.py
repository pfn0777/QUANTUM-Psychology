"""Prepare bot JPEG assets and a compact coaching video from local sources."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/specs/instagram-media-manifest.json"
JPEG_QUALITY = 85
MAX_IMAGE_SIDE = 1280
MAX_IMAGE_BYTES = 1_000_000
MAX_VIDEO_BYTES = 12_000_000
UPSCALE_FACTOR = 2
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280
INITIAL_CRF = 28
MAX_CRF = 40
CRF_STEP = 3
AUDIO_BITRATE = "96k"
EXPECTED_COUNTS = {"reviews": 24, "about": 2}
IMAGE_TARGETS = {
    (ROOT / "bot/assets/reviews").resolve(): "reviews",
    (ROOT / "bot/assets/about").resolve(): "about",
}
VIDEO_TARGET = (ROOT / "bot/assets/coaching12.mp4").resolve()


def allowed_target(raw_target: str, allowed: set[Path], kind: str) -> Path:
    if not isinstance(raw_target, str):
        raise ValueError(f"Invalid {kind} target {raw_target!r}; expected a repo-relative path")
    relative = Path(raw_target)
    target = (ROOT / relative).resolve()
    if (relative.drive or relative.root or ".." in relative.parts or
            not target.is_relative_to(ROOT) or target not in allowed):
        choices = ", ".join(str(path.relative_to(ROOT)) for path in sorted(allowed) if path.is_relative_to(ROOT))
        raise ValueError(f"Invalid {kind} target {raw_target!r}; allowed: {choices} inside the repo (no path traversal)")
    return target


def media_plan(manifest: dict) -> dict[str, list[tuple[Path, tuple[int, ...] | None]]]:
    groups = manifest["groups"]
    plan = {"reviews": [], "about": []}
    for group_name in ("natijalar", "otziv", "asoschi"):
        target = IMAGE_TARGETS[allowed_target(groups[group_name]["target"], set(IMAGE_TARGETS), "image")]
        for entry in groups[group_name]["files"]:
            plan[target].append((ROOT / entry["file"], tuple(entry["crop"])))
    allowed_target(manifest["telegram_screenshots"]["target"], set(IMAGE_TARGETS), "image")
    for source in manifest["telegram_screenshots"]["files"]:
        plan["reviews"].append((ROOT / source, None))
    if [len(plan[name]) for name in EXPECTED_COUNTS] != list(EXPECTED_COUNTS.values()):
        raise ValueError("Manifest media counts differ from the expected bot order")
    return plan


def prepare_image(source: Path, crop: tuple[int, ...] | None, destination: Path) -> None:
    with Image.open(source) as original:
        if crop is not None:
            if len(crop) != 4 or not (0 <= crop[0] < crop[2] <= original.width and
                                           0 <= crop[1] < crop[3] <= original.height):
                raise ValueError(f"Invalid crop for {source}: {crop}")
            image = original.crop(crop)
            image = image.resize((image.width * UPSCALE_FACTOR, image.height * UPSCALE_FACTOR), Image.Resampling.LANCZOS)
        else:
            image = original.copy()
        if max(image.size) > MAX_IMAGE_SIDE:
            image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
        # A fresh RGB image prevents EXIF and other source metadata from propagating.
        rgb = Image.new("RGB", image.size, "white")
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            rgba = image.convert("RGBA")
            rgb.paste(rgba, mask=rgba.getchannel("A"))
        else:
            rgb.paste(image.convert("RGB"))
        rgb.save(destination, "JPEG", quality=JPEG_QUALITY, exif=b"")
    if destination.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError(f"JPEG exceeds 1 MB: {destination}")


def find_ffmpeg(override: str | None) -> tuple[str, str]:
    ffmpeg = override or shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg missing: install it or pass --ffmpeg PATH")
    ffmpeg_path = Path(ffmpeg)
    sibling = ffmpeg_path.with_name("ffprobe.exe" if ffmpeg_path.suffix.lower() == ".exe" else "ffprobe")
    ffprobe = str(sibling) if sibling.is_file() else shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe missing: place it next to ffmpeg or on PATH")
    return str(ffmpeg), ffprobe


def prepare_video(ffmpeg: str, source: Path, destination: Path) -> None:
    for crf in range(INITIAL_CRF, MAX_CRF + 1, CRF_STEP):
        subprocess.run([
            ffmpeg, "-y", "-i", str(source), "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}",
            "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
            "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-movflags", "+faststart",
            str(destination),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if destination.stat().st_size <= MAX_VIDEO_BYTES:
            return
        print(f"Video exceeds 12 MB at CRF {crf}; retrying", file=sys.stderr)
    raise ValueError(f"Video exceeds 12 MB even at CRF {MAX_CRF}")


def check_assets(plan: dict, ffprobe: str, video: Path) -> None:
    problems = []
    for name, entries in plan.items():
        folder = ROOT / "bot/assets" / name
        files = sorted(folder.glob("*.jpg"))
        expected = [f"{number:02d}.jpg" for number in range(1, len(entries) + 1)]
        if [file.name for file in files] != expected:
            problems.append(f"{name}: expected {len(entries)} numbered JPEGs, found {len(files)}")
        for file in files:
            if file.stat().st_size > MAX_IMAGE_BYTES:
                problems.append(f"{file}: exceeds 1 MB")
            try:
                with Image.open(file) as image:
                    image.verify()
                with Image.open(file) as image:
                    if image.format != "JPEG" or image.mode != "RGB" or max(image.size) > MAX_IMAGE_SIDE or image.getexif():
                        problems.append(f"{file}: invalid JPEG format, mode, dimensions or EXIF")
            except (OSError, ValueError) as exc:
                problems.append(f"{file}: {exc}")
        print(f"{name}: {len(files)} JPEGs")
    if not video.is_file():
        problems.append(f"Missing video: {video}")
    else:
        if video.stat().st_size > MAX_VIDEO_BYTES:
            problems.append(f"{video}: exceeds 12 MB")
        result = subprocess.run([ffprobe, "-v", "error", "-show_streams", "-of", "json", str(video)],
                                check=True, capture_output=True, text=True)
        streams = json.loads(result.stdout)["streams"]
        videos = [stream for stream in streams if stream["codec_type"] == "video"]
        audios = [stream for stream in streams if stream["codec_type"] == "audio"]
        if len(videos) != 1 or videos[0]["codec_name"] != "h264" or (videos[0]["width"], videos[0]["height"]) != (VIDEO_WIDTH, VIDEO_HEIGHT):
            problems.append("Video must have one h264 720x1280 stream")
        if len(audios) != 1 or audios[0]["codec_name"] != "aac":
            problems.append("Video must have one aac audio stream")
        print(f"video: {video.stat().st_size} bytes")
    if problems:
        raise ValueError("\n".join(problems))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate existing assets without writing")
    parser.add_argument("--ffmpeg", help="Path to ffmpeg executable")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plan = media_plan(manifest)
    video = allowed_target(manifest["video"]["target"], {VIDEO_TARGET}, "video")
    if not args.check:
        for name, entries in plan.items():
            folder = ROOT / "bot/assets" / name
            folder.mkdir(parents=True, exist_ok=True)
            for old in folder.glob("*.jpg"):
                old.unlink()
            for index, (source, crop) in enumerate(entries, start=1):
                prepare_image(source, crop, folder / f"{index:02d}.jpg")
            print(f"Prepared {len(entries)} {name} JPEGs")
    ffmpeg, ffprobe = find_ffmpeg(args.ffmpeg)
    if not args.check:
        prepare_video(ffmpeg, ROOT / manifest["video"]["source"], video)
    check_assets(plan, ffprobe, video)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Media preparation failed: {error}", file=sys.stderr)
        sys.exit(1)
