import edge_tts
import asyncio
import json
import os

class TextToAudio:
    def __init__(self, voice="te-IN-MohanNeural"):
        self.voice = voice

    async def _stream_to_file(self, text, file_handle, offset_base=0):
        """Streams a single block of text to an already open binary file."""
        communicate = edge_tts.Communicate(text, self.voice)
        word_timestamps = []
        chunks = 0
        
        async for chunk in communicate.stream():
            # In some versions of edge-tts, the type is 'audio', in others 'data'
            if chunk["type"] == "audio":
                file_handle.write(chunk["data"])
                chunks += 1
            elif chunk["type"] == "data":
                file_handle.write(chunk["data"])
                chunks += 1
            elif chunk["type"] == "WordBoundary":
                start_time = chunk["offset"] / 10**7
                duration = chunk["duration"] / 10**7
                word_timestamps.append({
                    "text": chunk["text"],
                    "start": round(start_time + offset_base, 3),
                    "end": round(start_time + duration + offset_base, 3),
                })
        return word_timestamps, chunks

    async def convert_all_to_single_file(self, input_json_path, output_audio_path):
        if not os.path.exists(input_json_path):
            print(f"Error: {input_json_path} not found.")
            return

        with open(input_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            print("Error: JSON file is empty.")
            return

        print(f"Found {len(data)} segments. Generating audio...")
        
        all_word_timestamps = []
        total_chunks = 0
        current_offset = 0
        
        try:
            with open(output_audio_path, "wb") as f:
                # Process in batches of 15 segments for better reliability
                batch_size = 15
                for i in range(0, len(data), batch_size):
                    batch = data[i : i + batch_size]
                    batch_text = " ".join([item["text"] for item in batch])
                    
                    print(f"Converting segments {i+1} to {min(i+batch_size, len(data))} of {len(data)}...")
                    
                    if i > 0:
                        await asyncio.sleep(0.5)
                        
                    timestamps, chunks = await self._stream_to_file(batch_text, f, current_offset)
                    all_word_timestamps.extend(timestamps)
                    total_chunks += chunks
                    
                    if timestamps:
                        # Set next offset to the end of last word, plus a tiny gap
                        current_offset = timestamps[-1]["end"] + 0.1
            
            if total_chunks == 0:
                print("FAILED: No audio data was captured. Ensure your internet connection is active.")
                return

            # Save word-level timestamps
            metadata_path = "audio_timestamps.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump({
                    "audio_file": output_audio_path,
                    "voice": self.voice,
                    "word_timestamps": all_word_timestamps
                }, f, indent=2, ensure_ascii=False)
                
            print(f"\nSUCCESS!")
            print(f"Audio File: {os.path.abspath(output_audio_path)}")
            print(f"File Size: {os.path.getsize(output_audio_path)} bytes")
            print(f"Metadata: {os.path.abspath(metadata_path)}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    INPUT_JSON = "translated_text.json"
    OUTPUT_MP3 = "output_combined.mp3"
    
    engine = TextToAudio(voice="te-IN-MohanNeural") 
    
    # Use a clean event loop to avoid 'Task was destroyed' errors
    async def main():
        await engine.convert_all_to_single_file(INPUT_JSON, OUTPUT_MP3)
    
    asyncio.run(main())
