# from transformers import pipeline
import json
from transformers import AutoTokenizer, M2M100ForConditionalGeneration
from transformers import M2M100Tokenizer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class textConversion:
    def __init__(self,src):
        self.src=src
    
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
        with open(trans_txt, "w", encoding="utf-8") as f:
            json.dump(trans_seg, f, ensure_ascii=False, indent=2)
        return trans_seg
    
    def convert_with_sarvam(self):
        import requests
        url = "https://api.sarvam.ai/translate"
    
        payload = {
            "input": text,
            "source_language": source_lang,
            "target_language": target_lang
        }
    
        headers = {
            "Authorization": "Bearer YOUR_API_KEY"
        }
    
        response = requests.post(url, json=payload, headers=headers)
        return response.json()["translated_text"]


if __name__=="__main__":
    textConversion("source_text.json").convert()