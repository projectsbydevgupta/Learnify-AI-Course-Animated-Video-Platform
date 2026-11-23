import os
import asyncio
import subprocess
import wave
import edge_tts
from mutagen.mp3 import MP3

PUBLIC_AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../video-engine/public/audio"))

def _generate_offline_windows_sapi(text: str, output_path: str) -> float:
    """Fallback: Generates offline WAV audio using Windows native SpeechSynthesizer."""
    try:
        clean_text = text.replace("'", "''").replace('"', '`"').replace("\n", " ")
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.SetOutputToWaveFile('{output_path}'); "
            f"$synth.Speak('{clean_text}'); "
            f"$synth.Dispose()"
        )
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=15)
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with wave.open(output_path, 'r') as w:
                frames = w.getnframes()
                rate = w.getframerate()
                return round(frames / float(rate), 2)
    except Exception as e:
        print(f"[TTS Fallback Notice]: Windows SAPI offline speech failed: {e}")
    return 0.0

async def generate_scene_audio_async(scene_id: str, narration_text: str, topic_id: str, sem: asyncio.Semaphore) -> tuple[str | None, float]:
    """Generates TTS audio file with retries and automatic offline/cadence fallback."""
    os.makedirs(PUBLIC_AUDIO_DIR, exist_ok=True)
    
    file_name = f"narration_{topic_id}_scene_{scene_id}.mp3"
    full_path = os.path.join(PUBLIC_AUDIO_DIR, file_name)
    voice = os.getenv("TTS_VOICE", "en-US-GuyNeural")

    # 1. Primary: Edge-TTS with 3 retries & semaphore rate limiting
    async with sem:
        for attempt in range(1, 4):
            try:
                communicate = edge_tts.Communicate(narration_text, voice, rate="+0%", pitch="+0Hz")
                await communicate.save(full_path)
                
                if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                    audio = MP3(full_path)
                    duration_sec = round(audio.info.length, 2)
                    return f"audio/{file_name}", duration_sec
            except Exception as ex:
                print(f"[TTS Warning] Edge-TTS attempt {attempt}/3 failed for scene {scene_id}: {ex}")
                await asyncio.sleep(1.0)

    # 2. Secondary Fallback: Windows SAPI Offline Speech (0 network required)
    wav_file_name = f"narration_{topic_id}_scene_{scene_id}.wav"
    wav_full_path = os.path.join(PUBLIC_AUDIO_DIR, wav_file_name)
    print(f"[TTS Fallback] Activating Windows offline SAPI synthesizer for scene {scene_id}...")
    sapi_dur = _generate_offline_windows_sapi(narration_text, wav_full_path)
    if sapi_dur > 0:
        return f"audio/{wav_file_name}", sapi_dur

    # 3. Tertiary Safe Cadence Fallback (Guarantees Celery NEVER crashes)
    estimated_duration = max(4.0, round(len(narration_text.split()) / 2.5, 2))
    print(f"[TTS Fallback] Using estimated cadence ({estimated_duration}s) for scene {scene_id}.")
    return None, estimated_duration

async def _generate_all_scenes_audio(topic_id: str, scenes: list[dict]) -> list[tuple[str | None, float]]:
    sem = asyncio.Semaphore(3)  # Max 3 concurrent requests to avoid DNS/handshake spikes
    tasks = []
    for idx, scene in enumerate(scenes):
        narration = scene.get("narration", "").strip()
        scene_id = scene.get("scene_id", idx + 1)
        if narration:
            tasks.append(generate_scene_audio_async(str(scene_id), narration, topic_id, sem))
        else:
            async def _dummy():
                return None, 0.0
            tasks.append(_dummy())
    return await asyncio.gather(*tasks)

def process_tts_and_sync_scenes(topic_id: str, scenes: list[dict]) -> list[dict]:
    """
    Concurrently generates audio for all scene narrations in parallel and recalculates
    scene timing to match exact spoken audio length + padding buffer.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(_generate_all_scenes_audio(topic_id, scenes))
    finally:
        loop.close()

    current_time = 0.0
    synced_scenes = []

    for scene, (relative_audio, duration) in zip(scenes, results):
        if relative_audio and duration > 0:
            scene_duration = max(3.0, duration + 0.4)
        else:
            scene_duration = max(3.5, duration if duration > 0 else 3.5)

        scene["audio_src"] = relative_audio
        scene["start_time"] = round(current_time, 2)
        scene["end_time"] = round(current_time + scene_duration, 2)
        current_time += scene_duration
        synced_scenes.append(scene)

    return synced_scenes