import whisper
import json
class AudioTOText:
    def __init__(self,audio_path):
        self.audio_path=audio_path

    def convert(self):
        src="source_text.json"
        model = whisper.load_model("base")
        result = model.transcribe(self.audio_path)
        segments=[]
        for segment in result["segments"]:
            segments.append({"start":segment["start"],"end":segment["end"],"text":segment["text"]})
        with open(src, "w") as f:
            json.dump(segments,f)  
        return src

if __name__=="__main__":
    AudioTOText("audio.wav").convert()
