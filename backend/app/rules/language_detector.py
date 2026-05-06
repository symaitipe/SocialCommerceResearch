import re

SINHALA_PATTERN = re.compile(r'[\u0D80-\u0DFF]')

SINGLISH_KEYWORDS = [
    "kohomada", "kiyala", "denna", "eka", "karanna", "wage", "tika",
    "hadala", "ekata", "awilla", "enne", "ganna", "yan", "oyage",
    "mama", "api", "oya", "meka", "danne", "inne", "witharai",
    "mokakda", "kawda", "koheda", "hari", "neda", "nam", "puluwan"
]

def detect_language(text: str) -> str:
    text_lower = text.lower()
    has_sinhala = bool(SINHALA_PATTERN.search(text))
    has_english = bool(re.search(r'[a-zA-Z]', text))
    singlish_score = sum(1 for word in SINGLISH_KEYWORDS if word in text_lower)

    if has_sinhala and has_english:
        return "mixed"
    if has_sinhala and not has_english:
        return "sinhala"
    if has_english and singlish_score >= 1:
        return "singlish"
    return "english"