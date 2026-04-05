import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, CompositeAudioClip
import librosa
import soundfile as sf
import json

class VideoAudioSyncEngine:
    def __init__(self, video_path, transcript_path):
        self.video_path = video_path
        self.video = VideoFileClip(video_path)
        self.fps = self.video.fps
        
        with open(transcript_path, 'r', encoding='utf-8') as f:
            self.transcript = json.load(f)
    
    def sync_audio_to_video(self, audio_segments, output_path):
        """
        Sync multiple audio segments to video
        audio_segments: list of {"path": "file.wav", "start": 0.0, "end": 2.0}
        """
        audio_clips = []
        
        for segment in audio_segments:
            audio = AudioFileClip(segment['path'])
            # Adjust duration to match transcript timing
            duration = segment['end'] - segment['start']
            
            # Speed up/slow down audio to fit timing
            if audio.duration != duration:
                audio = audio.speedx(audio.duration / duration)
            
            # Position audio at correct timestamp
            audio = audio.set_start(segment['start'])
            audio_clips.append(audio)
        
        # Composite all audio clips
        final_audio = CompositeAudioClip(audio_clips)
        
        # Merge with video
        final_video = self.video.set_audio(final_audio)
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
    
    def align_speech_to_timing(self, audio_path, target_duration):
        """Stretch/compress audio to fit exact timing"""
        y, sr = librosa.load(audio_path)
        
        # Calculate stretch factor
        current_duration = librosa.get_duration(y=y, sr=sr)
        stretch_factor = current_duration / target_duration
        
        # Apply time stretching (preserves pitch)
        y_stretched = librosa.effects.time_stretch(y, rate=stretch_factor)
        
        return y_stretched, sr
    
    def create_smooth_transitions(self, audio_segments, crossfade_duration=0.2):
        """Add crossfade between segments for smooth transitions"""
        combined = np.array([])
        sr = 16000  # Standard sample rate
        
        for i, segment in enumerate(audio_segments):
            y, sr = librosa.load(segment['path'], sr=sr)
            
            if i > 0 and crossfade_duration > 0:
                # Crossfade with previous segment
                fade_samples = int(crossfade_duration * sr)
                
                # Fade out end of previous
                combined[-fade_samples:] *= np.linspace(1, 0, fade_samples)
                # Fade in start of current
                y[:fade_samples] *= np.linspace(0, 1, fade_samples)
            
            combined = np.concatenate([combined, y])
        
        return combined, sr

# Usage
sync_engine = VideoAudioSyncEngine("video.mp4", "transcript.json")

# Process each segment
audio_segments = []
for item in transcript:
    # Generate speech (using any TTS method above)
    audio_path = f"generated_{item['start']}.wav"
    
    # Align to exact timing
    y, sr = sync_engine.align_speech_to_timing(audio_path, item['end'] - item['start'])
    
    audio_segments.append({
        'path': audio_path,
        'start': item['start'],
        'end': item['end']
    })

# Sync to video
sync_engine.sync_audio_to_video(audio_segments, "final_output.mp4")