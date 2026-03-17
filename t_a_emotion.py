import json
import torch
import torchaudio
import numpy as np
import soundfile as sf

from transformers import (
    SpeechT5Processor,
    SpeechT5ForTextToSpeech,
    SpeechT5HifiGan
)

from speechbrain.inference import EncoderClassifier


class EmotionAwareTTS:

    def __init__(self, reference_audio):

        # Load models
        self.processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
        self.model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
        self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

        self.encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-xvect-voxceleb"
        )

        # Extract speaker embedding
        self.speaker_embedding = self._get_speaker_embedding(reference_audio)

    def _get_speaker_embedding(self, audio_path):

        waveform, sr = torchaudio.load(audio_path)

        embedding = self.encoder.encode_batch(waveform)[:1]

        embedding = embedding.squeeze().unsqueeze(0)

        return embedding
    def split_text(self,text, max_words=20):

        words = text.split()
        chunks = []

        for i in range(0, len(words), max_words):
            chunks.append(" ".join(words[i:i+max_words]))

        return chunks
    
    def generate_speech(self, text):

        chunks = self.split_text(text)

        outputs = []

        for chunk in chunks:

            inputs = self.processor(text=chunk, return_tensors="pt")

            speech = self.model.generate_speech(
                inputs["input_ids"],
                self.speaker_embedding,
                vocoder=self.vocoder,
                maxlenratio=8
            )

            outputs.append(speech.numpy())

        return np.concatenate(outputs)

    def load_json(self, json_path):

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def generate_segments(self, json_path):

        segments = self.load_json(json_path)

        audio_segments = []

        for seg in segments:

            text = seg["text"]
            start = seg["start"]
            end = seg["end"]
            print(text)
            print("-"*20)

            speech = self.generate_speech(text)

            audio_segments.append({
                "start": start,
                "end": end,
                "audio": speech
            })

        return audio_segments

    def combine_segments(self, audio_segments, sample_rate=16000):

        final_audio = np.array([], dtype=np.float32)

        for seg in audio_segments:

            start_sample = int(seg["start"] * sample_rate)

            if len(final_audio) < start_sample:
                padding = np.zeros(start_sample - len(final_audio))
                final_audio = np.concatenate([final_audio, padding])

            final_audio = np.concatenate([final_audio, seg["audio"]])

        return final_audio

    def generate_audio_from_json(self, json_path, output_file):

        segments = self.generate_segments(json_path)

        final_audio = self.combine_segments(segments)

        sf.write(output_file, final_audio, 16000)

        print("Audio saved to:", output_file)

if __name__ == "__main__":
    tts = EmotionAwareTTS("audio.wav")
    tts.generate_audio_from_json("translated_text.json", "output.wav")