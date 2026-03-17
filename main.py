# v-v\Scripts\activate.ps1 
from v_a import videotoaudio
from a_t import AudioTOText
from t_t import textConversion
from t_a import TextToAudio

if __name__=="__main__":
    #audio extraction
    video_path="video3[cry].mp4"
    OUTPUT_MP3 = "output_combined.mp3"
    src_audio=videotoaudio(video_path).convert()

    #text extraction
    src_text=AudioTOText(src_audio).convert()
    #text translation

    dst_text=textConversion(src_text).convert()
    
    #audio translation
    # ta=TextToAudio(voice="te-IN-MohanNeural")
    # async def main():
    #     await ta.convert_all_to_single_file(dst_text, OUTPUT_MP3)
    # asyncio.run(main())