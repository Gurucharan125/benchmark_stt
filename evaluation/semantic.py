from evaluation.wer import calculate_wer

def calculate_semantic_wer(
    reference: str,
    hypothesis: str,
) -> float:
    # SemWER and WER are now identical because we upgraded the base 
    # calculate_wer to use the robust OpenAI Whisper normalizer, which 
    # standardizes all text semantically (numbers, currency, etc).
    return calculate_wer(reference, hypothesis)