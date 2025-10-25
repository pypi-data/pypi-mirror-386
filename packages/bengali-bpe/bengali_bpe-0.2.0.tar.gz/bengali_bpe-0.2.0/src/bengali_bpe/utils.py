import unicodedata
import re

def normalize_bengali_text(text):
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
