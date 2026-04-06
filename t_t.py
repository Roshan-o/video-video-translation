# from transformers import pipeline
from aiohttp import client
import json
from transformers import AutoTokenizer
# from transformers import M2M100Tokenizer
from transformers import AutoModelForSeq2SeqLM
from sarvamai import SarvamAI

class textConversion:
    def __init__(self, src, dest="output/translated_text.json"):
        self.src = src
        self.dest = dest
    
    def convert(self):
        trans_txt="translated_text.json"
        with open(self.src,"r") as f:
            data=json.load(f)
        model_name = "facebook/nllb-200-distilled-600M"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        src_text=[]
        for i in data:
            src_text.append(i["text"])

        tokenizer.src_lang = "en"
        # encoded = tokenizer(src_text, return_tensors="pt")
        encoded = tokenizer(
            src_text,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        # print(tokenizer.lang_code_to_token.keys())
        generated_tokens = model.generate(
            **encoded,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids("tel_Telu")
        )
        translated_text = tokenizer.batch_decode(generated_tokens,
                                                 skip_special_tokens=True)
        trans_seg=[]
        for i in range(len(translated_text)):
            trans_seg.append({"start":data[i]["start"],"end":data[i]["end"],"text":translated_text[i]})
        with open(self.dest, "w", encoding="utf-8") as f:
            json.dump(trans_seg, f, ensure_ascii=False, indent=2)
        return trans_seg
    
    def convert_with_sarvam(self, api_key):
        from sarvamai import SarvamAI
        from concurrent.futures import ThreadPoolExecutor
        
        with open(self.src, "r") as f:
            data = json.load(f)
            
        # Initialize the official SarvamAI client
        client = SarvamAI(api_subscription_key=api_key)

        def translate_segment(segment):
            try:
                # Use the SDK as requested
                response = client.text.translate(
                    input=segment["text"],
                    source_language_code="en-IN",
                    target_language_code="te-IN",
                    model="mayura:v1"
                )
                return {
                    "start": segment["start"], 
                    "end": segment["end"], 
                    "text": response.translated_text
                }
            except Exception as e:
                print(f"Exception for segment {segment['start']}: {e}")
                return segment

        # Maximize speed by translating segments concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            trans_seg = list(executor.map(translate_segment, data))

        with open(self.dest, "w", encoding="utf-8") as f:
            json.dump(trans_seg, f, ensure_ascii=False, indent=2)
            
        return trans_seg


if __name__=="__main__":
    # textConversion("source_text.json").convert()
    textConversion("output/source_text.json").convert_with_sarvam("sk_omffrun1_uVmCyExpF9xp9Atcfni45GS4")