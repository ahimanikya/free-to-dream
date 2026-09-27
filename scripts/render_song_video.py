#!/usr/bin/env python3
"""Fit shared visuals to a selected song without changing audio speed or pitch."""
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', type=Path, required=True)
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--language', default='und', help='ISO 639-2 audio language code')
    parser.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error('Install FFmpeg or pass --ffmpeg /path/to/ffmpeg')
    if args.output.exists() or args.work_dir.exists():
        parser.error('Use a new output and work directory; existing versions are preserved.')
    for path in (args.audio, args.video):
        if not path.is_file():
            parser.error(f'Missing media: {path}')
        with path.open('rb') as stream:
            if stream.read(100).startswith(b'version https://git-lfs.github.com/spec/'):
                parser.error(f'Download the Git LFS media first: {path}')
    args.work_dir.mkdir(parents=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = args.ffmpeg

    def samples(path, rate):
        raw = subprocess.check_output([ffmpeg, '-v', 'error', '-xerror', '-i', str(path),
            '-map', '0:a:0', '-ac', '1', '-ar', str(rate), '-f', 's16le', '-'])
        result = array('h')
        result.frombytes(raw)
        return result

    duration = len(samples(args.audio, 48000)) / 48000
    probe = subprocess.run([ffmpeg, '-hide_banner', '-i', str(args.video)], capture_output=True, text=True)
    match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', probe.stderr)
    if not match or 'Video:' not in probe.stderr:
        raise ValueError('Cannot determine source video duration.')
    hours, minutes, seconds = map(float, match.groups())
    video_seconds = hours * 3600 + minutes * 60 + seconds
    if duration <= 0 or video_seconds <= 0:
        raise ValueError('Inputs must have positive durations.')
    factor = duration / video_seconds
    command = [ffmpeg, '-hide_banner', '-nostdin', '-n', '-i', str(args.video),
        '-i', str(args.audio), '-map', '0:v:0', '-map', '1:a:0', '-vf',
        f'setpts={factor:.12f}*(PTS-STARTPTS),fps=30,scale=in_range=full:out_range=tv,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.1',
        '-t', str(duration), '-c:v', 'libx264', '-threads', '4', '-preset', 'fast',
        '-crf', '19', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-map_metadata', '-1',
        '-metadata', f'title={args.title}', '-metadata:s:a:0', f'language={args.language}',
        '-movflags', '+faststart', str(args.output)]
    (args.work_dir / 'command.json').write_text(json.dumps(command, indent=2))
    print(f'Rendering {duration:.3f}s; visual duration factor {factor:.6f}', flush=True)
    with (args.work_dir / 'encode.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=log, check=True)
    subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(args.output),
        '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'], check=True)
    original, rendered = samples(args.audio, 8000), samples(args.output, 8000)
    count = min(len(original), len(rendered))
    a, b = original[:count:8], rendered[:count:8]
    energy = math.sqrt(sum(x*x for x in a) * sum(y*y for y in b))
    correlation = sum(x*y for x, y in zip(a, b)) / energy if energy else 0
    if correlation < .99 or abs(len(rendered) / 8000 - duration) > .1:
        raise ValueError('Rendered soundtrack does not sufficiently match the selected audio.')
    for label, second in [('opening', 0), ('middle', duration/2), ('ending', duration-.5)]:
        subprocess.run([ffmpeg, '-v', 'error', '-n', '-ss', str(second), '-i', str(args.output),
            '-frames:v', '1', '-update', '1', str(args.work_dir / f'{label}.jpg')], check=True)
    report = dict(full_decode='passed', audio_sha256=hashlib.sha256(args.audio.read_bytes()).hexdigest(),
        source_audio_seconds=duration, output_audio_seconds=len(rendered)/8000,
        video_source_sha256=hashlib.sha256(args.video.read_bytes()).hexdigest(),
        video_time_factor=factor, audio_correlation=correlation, output_bytes=args.output.stat().st_size,
        output_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest())
    (args.work_dir / 'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
