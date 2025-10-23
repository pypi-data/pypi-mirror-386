"""Main processing pipeline orchestration."""

import logging
from pathlib import Path

from slidegeist.constants import (
    DEFAULT_DEVICE,
    DEFAULT_IMAGE_FORMAT,
    DEFAULT_MIN_SCENE_LEN,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SCENE_THRESHOLD,
    DEFAULT_START_OFFSET,
    DEFAULT_WHISPER_MODEL,
)
from slidegeist.export import export_slides_json
from slidegeist.ffmpeg import detect_scenes
from slidegeist.slides import extract_slides
from slidegeist.transcribe import transcribe_video

logger = logging.getLogger(__name__)


def process_video(
    video_path: Path,
    output_dir: Path,
    scene_threshold: float = DEFAULT_SCENE_THRESHOLD,
    min_scene_len: float = DEFAULT_MIN_SCENE_LEN,
    start_offset: float = DEFAULT_START_OFFSET,
    model: str = DEFAULT_WHISPER_MODEL,
    device: str = DEFAULT_DEVICE,
    image_format: str = DEFAULT_IMAGE_FORMAT,
    skip_slides: bool = False,
    skip_transcription: bool = False
) -> dict[str, Path | list[Path]]:
    """Process a video and return generated artifacts.

    Returns dictionary always containing ``output_dir`` and optionally:

    * ``slides`` – list of slide image paths when slides are extracted
    * ``slides_json`` – path to slides.json when transcription and slide
      extraction both succeed

    Raises:
        FileNotFoundError: If video file does not exist.
        Exception: For failures in downstream processing stages.
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Use video filename (without extension) as default output directory
    if output_dir == Path(DEFAULT_OUTPUT_DIR):
        output_dir = Path.cwd() / video_path.stem

    logger.info(f"Processing video: {video_path}")
    logger.info(f"Output directory: {output_dir}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, Path | list[Path]] = {
        'output_dir': output_dir
    }

    # Step 1: Scene detection (needed for slides)
    slide_metadata: list[tuple[int, float, float, Path]] = []
    scene_timestamps: list[float] = []
    if not skip_slides:
        logger.info("=" * 60)
        logger.info("STEP 1: Scene Detection")
        logger.info("=" * 60)

        scene_timestamps = detect_scenes(
            video_path,
            threshold=scene_threshold,
            min_scene_len=min_scene_len,
            start_offset=start_offset
        )

        if not scene_timestamps:
            logger.warning("No scene changes detected. Extracting single slide.")

        # Step 2: Extract slides into output directory
        logger.info("=" * 60)
        logger.info("STEP 2: Slide Extraction")
        logger.info("=" * 60)

        slide_metadata = extract_slides(
            video_path,
            scene_timestamps,
            output_dir,
            image_format
        )
        results['slides'] = [path for _, _, _, path in slide_metadata]

    # Step 3: Transcription
    transcript_segments = []
    if not skip_transcription:
        logger.info("=" * 60)
        logger.info("STEP 3: Audio Transcription")
        logger.info("=" * 60)

        transcript_data = transcribe_video(
            video_path,
            model_size=model,
            device=device
        )
        transcript_segments = transcript_data['segments']

    # Step 4: Export slides.json (requires both slides and transcription)
    if not skip_slides and not skip_transcription:
        logger.info("=" * 60)
        logger.info("STEP 4: Export slides.json")
        logger.info("=" * 60)

        json_path = output_dir / "slides.json"
        export_slides_json(
            video_path,
            slide_metadata,
            transcript_segments,
            json_path,
            model
        )
        results['slides_json'] = json_path

    # Summary
    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 60)
    if not skip_slides:
        logger.info(f"✓ Extracted {len(slide_metadata)} slides")
    if not skip_transcription:
        logger.info("✓ Transcribed audio")
    if not skip_slides and not skip_transcription:
        logger.info("✓ Created slides.json with transcript")
    logger.info(f"✓ All outputs in: {output_dir}")

    return results


def process_slides_only(
    video_path: Path,
    output_dir: Path,
    scene_threshold: float = DEFAULT_SCENE_THRESHOLD,
    min_scene_len: float = DEFAULT_MIN_SCENE_LEN,
    start_offset: float = DEFAULT_START_OFFSET,
    image_format: str = DEFAULT_IMAGE_FORMAT
) -> dict:
    """Extract only slides from video (no transcription).

    Args:
        video_path: Path to the input video file.
        output_dir: Directory where slide images will be saved.
        scene_threshold: Scene detection threshold (0-1 scale, lower = more sensitive).
        min_scene_len: Minimum scene length in seconds.
        start_offset: Skip first N seconds to avoid setup noise.
        image_format: Output image format (jpg or png).

    Returns:
        Dictionary containing ``output_dir`` and ``slides`` entries.
    """
    logger.info("Extracting slides only (no transcription)")
    result = process_video(
        video_path,
        output_dir,
        scene_threshold=scene_threshold,
        min_scene_len=min_scene_len,
        start_offset=start_offset,
        image_format=image_format,
        skip_transcription=True
    )
    return result
