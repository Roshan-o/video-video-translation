import json
from gtts import gTTS
from pydub import AudioSegment
import subprocess
import os

json_file = "translated_text.json"
video_file = "video3[cry].mp4"
output_video = "output_telugu_without_emotion.mp4"


with open(json_file, "r", encoding="utf-8") as f:
    segments = json.load(f)

# Total duration
total_duration = max(seg["end"] for seg in segments) * 1000
final_audio = AudioSegment.silent(duration=total_duration)

temp_files = []

for i, seg in enumerate(segments):
    text = seg["text"]
    start_time = int(seg["start"] * 1000)

    # Telugu TTS
    tts = gTTS(text=text, lang='te')  #
    temp_file = f"temp_{i}.mp3"
    tts.save(temp_file)
    temp_files.append(temp_file)

    speech = AudioSegment.from_mp3(temp_file)

    # Match duration
    target_duration = int((seg["end"] - seg["start"]) * 1000)

    if len(speech) > target_duration:
        speech = speech[:target_duration]
    else:
        silence = AudioSegment.silent(duration=target_duration - len(speech))
        speech += silence

    final_audio = final_audio.overlay(speech, position=start_time)

# Export audio
final_audio_file = "final_telugu_audio.wav"
final_audio.export(final_audio_file, format="wav")

# Merge with video
command = [
    "ffmpeg",
    "-i", video_file,
    "-i", final_audio_file,
    "-c:v", "copy",
    "-c:a", "aac",
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-shortest",
    output_video
]

subprocess.run(command)

# Cleanup
for f in temp_files:
    os.remove(f)

print("Telugu dubbed video generated!")