import subprocess


def extract_thumbnail(input_path, output_path, second=1):
    """
    Extract a single frame from input_path at the given second and
    save it as a JPEG at output_path.
    Raises CalledProcessError if ffmpeg exits with a non-zero status.
    """
    command = [
        'ffmpeg',
        '-y',
        '-ss', str(second),
        '-i', input_path,
        '-vframes', '1',
        output_path,
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def run_ffmpeg_hls(input_path, output_dir, width, height):
    """
    Convert input_path to an HLS rendition at the given resolution,
    writing index.m3u8 and .ts segments into output_dir.
    Raises CalledProcessError if ffmpeg exits with a non-zero status.
    """
    command = _build_ffmpeg_command(input_path, output_dir, width, height)
    subprocess.run(command, check=True, capture_output=True, text=True)


def _build_ffmpeg_command(input_path, output_dir, width, height):
    """Build the ffmpeg CLI argument list for a single-resolution HLS conversion."""
    return [
        'ffmpeg',
        '-i', input_path,
        '-vf', f'scale=w={width}:h={height}:force_original_aspect_ratio=decrease',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-ar', '48000',
        '-c:v', 'h264',
        '-profile:v', 'main',
        '-crf', '20',
        '-sc_threshold', '0',
        '-g', '48',
        '-keyint_min', '48',
        '-hls_time', '4',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', f'{output_dir}/%03d.ts', f"{output_dir}/index.m3u8"
    ]