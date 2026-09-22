"""Answer coding (BRD 3.9): case-insensitive substring match against the
vocab, no morphological analysis (BRD допущение 4 — kept deliberately simple).
"""

# Codes shared with the frontend / XLSX export (BRD 4.1).
CORRECT = 1
INCORRECT = 0
SKIPPED = 2
ERROR = 3


def code_response(recognized_text: str, vocab_words: list[str]) -> int:
    """CORRECT if `recognized_text` contains any vocab word as a substring
    (case-insensitive), else INCORRECT. Callers handle SKIPPED/ERROR
    themselves (button press / speech-recognition failure, not a text match)."""
    text = (recognized_text or '').strip().lower()
    if not text or not vocab_words:
        return INCORRECT
    return CORRECT if any((w or '').strip().lower() in text for w in vocab_words) else INCORRECT
