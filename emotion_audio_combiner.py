# Load model directly
# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-to-speech", model="Amirhossein75/Emotion-Aware-TTS-Style-Transfer")


from transformers import AutoProcessor, AutoModelForTextToSpectrogram

processor = AutoProcessor.from_pretrained("Amirhossein75/Emotion-Aware-TTS-Style-Transfer")
model = AutoModelForTextToSpectrogram.from_pretrained("Amirhossein75/Emotion-Aware-TTS-Style-Transfer")


