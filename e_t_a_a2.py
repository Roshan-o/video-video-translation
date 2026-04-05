import asyncio
import edge_tts
import soundfile as sf
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import json
import os
import librosa
import numpy as np
import warnings
warnings.filterwarnings("ignore")

print("=" * 80)
print("TELUGU TTS WITH EMOTION PRESERVATION & VIDEO SYNC")
print("=" * 80)

# ============================================================================
# STEP 1: EMOTION EXTRACTION
# ============================================================================

class EmotionAnalyzer:
    """Extract emotion features from audio"""
    
    @staticmethod
    def analyze(audio_path):
        """Analyze emotion from original audio"""
        if not os.path.exists(audio_path):
            print(f"  ! {audio_path} not found, using NEUTRAL emotion")
            return EmotionAnalyzer.get_neutral_emotion()
        
        try:
            y, sr = librosa.load(audio_path)
            
            # Extract features
            energy = np.sqrt(np.mean(librosa.feature.melspectrogram(y=y, sr=sr) ** 2))
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            try:
                f0 = librosa.yin(y, fmin=80, fmax=400, sr=sr)
                pitch_mean = np.nanmean(f0)
                pitch_std = np.nanstd(f0)
            except:
                pitch_mean = 150
                pitch_std = 30
            
            # Classify emotion
            emotion = EmotionAnalyzer.classify_emotion(
                energy, spectral_centroid, pitch_mean
            )
            
            emotion_params = EmotionAnalyzer.emotion_to_parameters(
                energy, spectral_centroid, pitch_mean, pitch_std
            )
            
            print(f"  ✓ Detected: {emotion.upper()}")
            print(f"    - Energy: {energy:.2f}")
            print(f"    - Pitch: {pitch_mean:.1f} Hz")
            print(f"    - Spectral Centroid: {spectral_centroid:.1f} Hz")
            
            return emotion_params
        
        except Exception as e:
            print(f"  ! Error analyzing: {e}, using NEUTRAL")
            return EmotionAnalyzer.get_neutral_emotion()
    
    @staticmethod
    def classify_emotion(energy, spectral_centroid, pitch_mean):
        """Classify emotion based on features"""
        if energy > 0.7:
            if spectral_centroid > 2500:
                return "happy"
            else:
                return "angry"
        elif energy < 0.3:
            return "sad"
        else:
            return "neutral"
    
    @staticmethod
    def emotion_to_parameters(energy, spectral_centroid, pitch_mean, pitch_std):
        """Convert emotion features to TTS parameters"""
        
        # Pitch shift (semitones)
        # Happy: +3 to +5, Sad: -2 to -4, Angry: +2 to +3, Neutral: 0
        if energy > 0.7:
            if spectral_centroid > 2500:
                pitch_shift = 4  # Happy
                speed_factor = 1.2
                energy_scale = 1.4
            else:
                pitch_shift = 2  # Angry
                speed_factor = 1.3
                energy_scale = 1.6
        elif energy < 0.3:
            pitch_shift = -3  # Sad
            speed_factor = 0.8
            energy_scale = 0.6
        else:
            pitch_shift = 0  # Neutral
            speed_factor = 1.0
            energy_scale = 1.0
        
        return {
            'pitch_shift': pitch_shift,
            'speed_factor': speed_factor,
            'energy_scale': energy_scale,
            'emotion': 'happy' if energy > 0.7 and spectral_centroid > 2500 else (
                'angry' if energy > 0.7 else ('sad' if energy < 0.3 else 'neutral')
            )
        }
    
    @staticmethod
    def get_neutral_emotion():
        """Default neutral emotion"""
        return {
            'pitch_shift': 0,
            'speed_factor': 1.0,
            'energy_scale': 1.0,
            'emotion': 'neutral'
        }


# ============================================================================
# STEP 2: EMOTION APPLICATION
# ============================================================================

class EmotionApplier:
    """Apply emotion to generated speech"""
    
    @staticmethod
    def apply(audio_path, emotion_params, sr=22050):
        """Apply emotion parameters to audio"""
        try:
            y, sr = librosa.load(audio_path, sr=sr)
            
            # 1. Pitch shift
            if emotion_params['pitch_shift'] != 0:
                try:
                    y = librosa.effects.pitch_shift(
                        y, 
                        sr=sr, 
                        n_steps=emotion_params['pitch_shift']
                    )
                except Exception as e:
                    print(f"      ! Pitch shift failed: {e}")
            
            # 2. Time stretch (speed)
            if emotion_params['speed_factor'] != 1.0:
                try:
                    y = librosa.effects.time_stretch(
                        y, 
                        rate=emotion_params['speed_factor']
                    )
                except Exception as e:
                    print(f"      ! Speed adjustment failed: {e}")
            
            # 3. Energy scaling (volume)
            if emotion_params['energy_scale'] != 1.0:
                y = y * emotion_params['energy_scale']
            
            # Prevent clipping
            max_val = np.max(np.abs(y))
            if max_val > 1.0:
                y = y / max_val
            
            return y, sr
        
        except Exception as e:
            print(f"      ! Error applying emotion: {e}")
            # Return original
            y, sr = librosa.load(audio_path, sr=sr)
            return y, sr


# ============================================================================
# STEP 3: AUDIO ALIGNMENT
# ============================================================================

class AudioAligner:
    """Align audio to exact timing"""
    
    @staticmethod
    def align(audio_array, sr, target_duration):
        """Stretch/compress audio to fit exact timing"""
        try:
            current_duration = len(audio_array) / sr
            
            if current_duration == 0 or target_duration == 0:
                return audio_array
            
            stretch_factor = current_duration / target_duration
            
            # Only stretch if needed and factor is reasonable
            if abs(stretch_factor - 1.0) > 0.01:  # More than 1% difference
                aligned = librosa.effects.time_stretch(audio_array, rate=stretch_factor)
                return aligned
            
            return audio_array
        
        except Exception as e:
            print(f"      ! Alignment error: {e}")
            return audio_array


# ============================================================================
# STEP 4: SPEECH GENERATION
# ============================================================================

async def generate_telugu_speech(text, output_file):
    """Generate Telugu speech using Edge TTS"""
    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice="te-IN-MohanVoice",  # Telugu male voice
            rate="+0%"
        )
        await communicate.save(output_file)
        return True
    except Exception as e:
        print(f"      Generation error: {e}")
        return False


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    # Load transcript
    print("\n[1/5] Loading transcript...")
    try:
        with open("translated_text.json", encoding='utf-8') as f:
            transcript = json.load(f)
        print(f"  ✓ Loaded {len(transcript)} segments")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Extract emotion from original audio
    print("\n[2/5] Analyzing emotion from original audio...")
    emotion_params = EmotionAnalyzer.analyze("audio.wav")
    print(f"  → Emotion parameters: {emotion_params['emotion']}")
    print(f"    • Pitch shift: {emotion_params['pitch_shift']} semitones")
    print(f"    • Speed factor: {emotion_params['speed_factor']}x")
    print(f"    • Energy scale: {emotion_params['energy_scale']}x")
    
    # Create output directory
    os.makedirs("output_audio", exist_ok=True)
    
    # Generate speech with emotion
    print("\n[3/5] Generating Telugu speech with emotion...")
    audio_clips = []
    generated_count = 0
    
    for i, segment in enumerate(transcript):
        text = segment['text']
        start_time = segment['start']
        end_time = segment['end']
        duration = end_time - start_time
        
        print(f"  [{i+1}/{len(transcript)}] {text[:45]}...", end=" ", flush=True)
        
        try:
            # 1. Generate base audio
            output_file = f"output_audio/segment_{i:03d}.wav"
            success = asyncio.run(generate_telugu_speech(text, output_file))
            
            if not success:
                print("✗")
                continue
            
            # 2. Check if file was created and has content
            if not os.path.exists(output_file):
                print("✗ (no file)")
                continue
            
            file_size = os.path.getsize(output_file)
            if file_size < 1000:
                print(f"✗ (empty)")
                os.remove(output_file)
                continue
            
            # 3. Load generated audio
            y, sr = librosa.load(output_file, sr=22050)
            if len(y) == 0:
                print("✗ (corrupt)")
                continue
            
            # 4. Apply emotion
            y_emotional, sr = EmotionApplier.apply(output_file, emotion_params, sr=22050)
            
            # 5. Align to exact timing
            y_aligned = AudioAligner.align(y_emotional, sr, duration)
            
            # 6. Save final audio
            sf.write(output_file, y_aligned, sr)
            
            # 7. Create audio clip
            audio = AudioFileClip(output_file).set_start(start_time)
            audio_clips.append(audio)
            generated_count += 1
            
            print("✓")
        
        except Exception as e:
            print(f"✗ ({str(e)[:30]})")
    
    print(f"  → Generated: {generated_count}/{len(transcript)} segments")
    
    # Check if we have audio clips
    if len(audio_clips) == 0:
        print("\n✗ No audio generated!")
        return False
    
    # Load and sync with video
    print("\n[4/5] Loading video...")
    try:
        if not os.path.exists("input.mp4"):
            print("  ✗ input.mp4 not found!")
            return False
        
        video = VideoFileClip("input.mp4")
        print(f"  ✓ Video loaded ({video.duration:.1f}s)")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Render final video
    print("\n[5/5] Rendering final video...")
    try:
        final_audio = CompositeAudioClip(audio_clips)
        final_video = video.set_audio(final_audio)
        
        print("  Rendering... (this may take several minutes)")
        final_video.write_videofile(
            "output_telugu_tts_emotional.mp4",
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None,
            fps=24
        )
        
        # Cleanup
        video.close()
        final_video.close()
        for clip in audio_clips:
            clip.close()
        
        print("\n" + "=" * 80)
        print("✓ SUCCESS! Output saved: output_telugu_tts_emotional.mp4")
        print("=" * 80)
        return True
    
    except Exception as e:
        print(f"  ✗ Rendering error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)