import jiwer
try:
    from whisper_normalizer.english import EnglishTextNormalizer  # type: ignore
    normalizer = EnglishTextNormalizer()
except ImportError:
    # Fallback to basic transform if not installed
    normalizer = jiwer.Compose([
        jiwer.ToLowerCase(),
        jiwer.RemovePunctuation(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip(),
    ])

def calculate_wer(
    reference: str,
    hypothesis: str,
) -> float:
    norm_ref = normalizer(reference)
    norm_hyp = normalizer(hypothesis)
    return jiwer.wer(norm_ref, norm_hyp)