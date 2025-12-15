from transformers import pipeline
from core.utils.logger import get_logger
import os
os.environ["TRANSFORMERS_NO_TF_WARNING"] = "1"
os.environ["USE_TF"] = "0"

log = get_logger("summarizer")

# Load the summarization pipeline once
_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize(article_text: str, reliability_hint: str):
    if not article_text:
        return {
            "neutral_summary": "",
            "trust_index": 50,
            "reasoning": "No content provided"
        }

    try:
        # Ask the model for both summary and reasoning
        prompt = (
            "Write your response in the following format:\n"
            "Summary: <your 3-4 sentence factual summary>\n"
            "Reasoning: <brief explanation of why the content seems trustworthy or questionable>\n\n"
            f"Article:\n{article_text[:2000]}"
        )

        output = _summarizer(prompt, max_length=100, min_length=50, do_sample=False)[0]["summary_text"]

        # Split summary and reasoning if possible
        if "Reasoning:" in output:
            summary, reasoning = output.split("Reasoning:", 1)
        elif "Explanation:" in output:
            summary, reasoning = output.split("Explanation:", 1)
        else:
            summary, reasoning = output, "Model did not provide explicit reasoning."

        summary = summary.strip()
        reasoning = reasoning.strip()

        # Simple heuristic for trust index
        trust_index = 60
        if reliability_hint == "trusted":
            trust_index += 20
        elif reliability_hint == "bad":
            trust_index -= 20
        trust_index = max(0, min(100, trust_index))

        return {
            "neutral_summary": summary,
            "trust_index": trust_index,
            "reasoning": reasoning
        }

    except Exception as e:
        log.error(f"Summarization failed: {e}")
        return {
            "neutral_summary": "",
            "trust_index": 50,
            "reasoning": "Error in summarizer"
        }
