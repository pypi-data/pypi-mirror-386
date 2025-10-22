import os
import subprocess
import json

try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    HAS_FFMPEG = True
except (subprocess.CalledProcessError, FileNotFoundError):
    HAS_FFMPEG = False


def has_audio_stream(video_path: str) -> bool:
    if not HAS_FFMPEG or not os.path.exists(video_path):
        return False

    try:
        import cv2
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'a', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            return False

        try:
            data = json.loads(result.stdout)
            return len(data.get('streams', [])) > 0
        except json.JSONDecodeError:
            return False

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                cap.release()
                return False
            audio_fourcc = cap.get(cv2.CAP_PROP_AUDIO_STREAM)
            cap.release()
            return audio_fourcc != -1.0 and audio_fourcc != 0.0
        except:
            return False
