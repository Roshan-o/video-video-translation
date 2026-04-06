# v-v\Scripts\activate.ps1 
from v_a import videotoaudio
from a_t import AudioTOText
from t_t import textConversion
from t_a import TextToAudio

if __name__=="__main__":
    #audio extraction
    video_path="video3[cry].mp4"
    OUTPUT_MP3 = "output/output_combined.mp3"
    src_text_path="output/source_text.json"
    dst_text_path="output/translated_text.json"
    output_video = "output/output_telugu_without_emotion.mp4"

    #audio extraction
    videotoaudio(video_path,OUTPUT_MP3).convert()

    #text extraction
    AudioTOText(OUTPUT_MP3,src_text_path).convert()

    #text to text translation
    textConversion(src_text_path,dst_text_path).convert()

    #audio to video translation
    AudioTOVideo(dst_text_path,video_path,output_video).convert()