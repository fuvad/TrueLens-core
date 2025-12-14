from transformers import pipeline
from core.utils.logger import get_logger

log = get_logger("analyzer")

_sent = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

def analyze_bias(text: str):
    if not text:
        return {"bias_label":"unknown","bias_score":0.0}
    
    try:
        r = _sent(text[:512])[0]
        label = r["label"].lower()
        score = float(r["score"])
        
        if "negative" in label:
            b = -score
        elif "positive" in label:
            b = score
        else:
            b = 0.0
        return {"bias_label": label, "bias_score": round(b,3)}
    
    except Exception as e:
        log.error(f"Analyzer failed: {e}")
        return {"bias_label":"unknown","bias_score":0.0}
