import os
import json
import subprocess
from services.tts_service import process_tts_and_sync_scenes

VIDEO_ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../video-engine"))
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../static/videos"))

def render_remotion_from_synced_scenes(topic_id: str, synced_scenes: list[dict]) -> str:
    """
    Renders Remotion video from already TTS-synced scene data with live streaming output.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_mp4_path = os.path.join(OUTPUT_DIR, f"narrated_video_{topic_id}.mp4")
    
    temp_json_path = os.path.join(VIDEO_ENGINE_DIR, f"temp_props_{topic_id}.json")
    props_payload = {"scenes": synced_scenes}
    
    with open(temp_json_path, "w", encoding="utf-8") as f:
        json.dump(props_payload, f, indent=2)

    # Detect local remotion executable to avoid npx registry resolving overhead
    local_remotion = os.path.join(VIDEO_ENGINE_DIR, "node_modules", ".bin", "remotion.cmd" if os.name == "nt" else "remotion")
    use_local = os.path.exists(local_remotion)

    cpu_count = os.cpu_count() or 4
    # Utilize multi-core parallel rendering (e.g., 4 parallel Chromium processes on Ryzen 6-core/12-thread)
    optimal_concurrency = max(2, min(cpu_count // 2, 4))

    # High-Performance Profile: parallel workers, veryfast x264, jpeg buffers, bundle-cache, 720p HD scaling
    base_args = [
        "render",
        "CourseLessonVideo",
        output_mp4_path,
        f"--props={temp_json_path}",
        "--scale=0.6667",
        f"--concurrency={optimal_concurrency}",
        "--x264-preset=veryfast",
        "--image-format=jpeg",
        "--jpeg-quality=85",
        "--bundle-cache",
        "--gl=angle",
        "--crf=23",
        "--overwrite"
    ]

    if use_local:
        cmd = [local_remotion] + base_args
    else:
        cmd = ["npx.cmd" if os.name == "nt" else "npx", "remotion"] + base_args

    print(f"[Remotion Engine] Rendering Fast HD MP4 for '{topic_id}' ({optimal_concurrency} parallel workers, veryfast x264, bundle-cached)...", flush=True)

    def _execute_render(command):
        render_env = os.environ.copy()
        render_env["NODE_OPTIONS"] = "--max-old-space-size=2048"
        proc = subprocess.Popen(
            command,
            cwd=VIDEO_ENGINE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=render_env
        )
        if proc.stdout:
            for line in iter(proc.stdout.readline, ''):
                clean = line.strip()
                if clean:
                    print(f"   [Remotion] {clean}", flush=True)
            proc.stdout.close()
        return proc.wait()

    try:
        ret = _execute_render(cmd)
        if ret != 0:
            # Fallback without --gl=angle and scale=0.5 to ensure completion under severe memory pressure
            print("[Remotion Engine] Retrying with lightweight fallback (scale=0.5, software GL)...", flush=True)
            cmd_fallback = [c for c in cmd if c != "--gl=angle"]
            cmd_fallback = [c if not c.startswith("--scale=") else "--scale=0.5" for c in cmd_fallback]
            ret = _execute_render(cmd_fallback)
            if ret != 0:
                raise RuntimeError(f"Remotion render failed with exit code {ret}")

        print("[Remotion Engine] Render Completed Successfully!", flush=True)
    except Exception as e:
        print(f"[Remotion Error]: {e}", flush=True)
        raise RuntimeError(f"Remotion render failed: {e}")
    finally:
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)

    return output_mp4_path

def render_remotion_video_with_audio(topic_id: str, scene_plan: list[dict]) -> str:
    """
    1. Runs TTS pipeline to generate narration audio and sync scene timestamps.
    2. Renders Remotion video with voiceover audio.
    """
    print(f"[TTS Pipeline] Generating narration audio for topic '{topic_id}'...", flush=True)
    synced_scenes = process_tts_and_sync_scenes(topic_id, scene_plan)
    return render_remotion_from_synced_scenes(topic_id, synced_scenes)

# Alias for backwards compatibility
render_remotion_video = render_remotion_video_with_audio