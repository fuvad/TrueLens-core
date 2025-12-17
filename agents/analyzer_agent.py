from transformers import pipeline
from core.utils.logger import get_logger

log = get_logger("analyzer")

_sent = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment"
)

# ✅ ADD THIS LABEL MAP
LABEL_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive"
}

def analyze_bias(text: str):
    if not text:
        return {"bias_label": "unknown", "bias_score": 0.0}

    try:
        r = _sent(text[:512])[0]

        raw_label = r["label"]          # LABEL_0 / LABEL_1 / LABEL_2
        score = float(r["score"])

        bias_label = LABEL_MAP.get(raw_label, "unknown")

        # ✅ Bias score logic
        if bias_label == "negative":
            bias_score = -score
        elif bias_label == "positive":
            bias_score = score
        else:
            bias_score = 0.0

        return {
            "bias_label": bias_label,
            "bias_score": round(bias_score, 3)
        }

    except Exception as e:
        log.error(f"Analyzer failed: {e}")
        return {"bias_label": "unknown", "bias_score": 0.0}
