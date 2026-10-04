
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from app.rules.routing_guards import (
    detect_ai_only_risk,
    contains_mobile_number,
)

EVIDENCE: dict[tuple[str, str], int] = {
    ("Positive Feedback", "english"): 102,
    ("Positive Feedback", "singlish"): 48,
    ("Positive Feedback", "sinhala"): 41,
    ("Positive Feedback", "mixed"): 24,
    ("Positive Feedback", "emoji"): 7,
    ("Product Inquiry", "english"): 29,
    ("Product Inquiry", "singlish"): 35,
    ("Product Inquiry", "sinhala"): 12,
    ("Product Inquiry", "mixed"): 9,
    ("Purchase Intent", "english"): 15,
    ("Purchase Intent", "singlish"): 18,
    ("Purchase Intent", "sinhala"): 20,
    ("Purchase Intent", "mixed"): 1,
    ("Price Inquiry", "english"): 13,
    ("Price Inquiry", "singlish"): 26,
    ("Price Inquiry", "sinhala"): 12,
    ("Price Inquiry", "mixed"): 1,
    ("Delivery Inquiry", "english"): 5,
    ("Delivery Inquiry", "singlish"): 15,
    ("Delivery Inquiry", "sinhala"): 4,
    ("Delivery Inquiry", "mixed"): 4,
    ("Negative Feedback/Complaint", "english"): 30,
    ("Negative Feedback/Complaint", "singlish"): 14,
    ("Negative Feedback/Complaint", "sinhala"): 12,
    ("Negative Feedback/Complaint", "mixed"): 8,
    ("Location/Availability", "english"): 9,
    ("Location/Availability", "singlish"): 7,
    ("Location/Availability", "sinhala"): 0,
    ("Location/Availability", "mixed"): 0,
    ("Payment Method Inquiry", "english"): 5,
    ("Payment Method Inquiry", "singlish"): 9,
    ("Payment Method Inquiry", "sinhala"): 1,
    ("Payment Method Inquiry", "mixed"): 0,
    ("Noise/Off-topic", "english"): 7,
    ("Noise/Off-topic", "singlish"): 4,
    ("Noise/Off-topic", "sinhala"): 1,
    ("Noise/Off-topic", "mixed"): 2,
    ("Noise/Off-topic", "emoji"): 1,
}

EVIDENCE_HIGH = 5
EVIDENCE_LOW = 3
AI_ONLY_CATEGORIES = frozenset({
    "Warranty/Service Inquiry", "Contact Request", "Price Complaint", "Suggestion"
})
RULE_CATEGORIES = [
    "Purchase Intent", "Product Inquiry", "Price Inquiry", "Delivery Inquiry",
    "Location/Availability", "Payment Method Inquiry",
    "Positive Feedback", "Negative Feedback/Complaint", "Noise/Off-topic",
]

CONTEXT_AI_CATEGORIES = frozenset({"Order/Purchase Confirmation"})


def normalize(text: str) -> str:
    if text is None:
        return ""
    return unicodedata.normalize("NFC", str(text)).lower().strip()


SINHALA_RANGE = re.compile(r"[\u0D80-\u0DFF]")
LATIN_RANGE = re.compile(r"[a-zA-Z]")
EMOJI_RANGE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF\u2764\ufe0f]"
)

SINGLISH_MARKERS = {
    "kiyada", "kiyda", "keeyda", "kohomada", "kohomda", "kohmada", "gana",
    "gaana", "ganata", "mila", "salli", "keeyada", "kiyad",
    "oni", "one", "ona", "onee", "ganna", "gannawa", "aragena", "gatta",
    "gaththa", "genna", "matath", "mata", "mama", "mage", "denna",
    "thiyanawada", "tiyenawada", "thiyenawada", "thibeda", "thiyeda",
    "nedda", "ndda", "nadda", "naa", "nane", "nhane", "athi", "tyenne",
    "thinne", "tiyenne", "thiyanawa", "tiyenawa",
    "hodai", "hondai", "hodata", "hoda", "niyamai", "supiri", "suppa",
    "patta", "maru", "maretama", "marama", "awl", "awlk", "aulak",
    "savuththu", "sawuththu", "wada", "vada", "wadak", "kaduna",
    "dawas", "dws", "ewanna", "ewnwd", "hambune", "hambuna", "hamben",
    "aawa", "awa", "awilla", "enne", "yanawa", "ynwd", "damma", "demma",
    "kara", "kala", "karanne", "karanna", "krnne", "puluwanda", "puluwnda",
    "barida", "berida", "epa", "meka", "meeka", "ekak", "ekk", "eka",
    "machan", "machang", "bro", "aiye", "bn", "ban", "wage", "witharada",
    "witharai", "kenek", "kenkt", "monawada", "mkdd", "mokadda",
}


def detect_language(text: str) -> str:
    t = normalize(text)
    has_sinhala = bool(SINHALA_RANGE.search(t))
    has_latin = bool(LATIN_RANGE.search(t))
    has_emoji = bool(EMOJI_RANGE.search(t))
    if has_sinhala and has_latin:
        return "mixed"
    if has_sinhala:
        return "sinhala"
    if has_latin:
        tokens = set(re.findall(r"[a-z]+", t))
        return "singlish" if tokens & SINGLISH_MARKERS else "english"
    if has_emoji:
        return "emoji"
    return "emoji" if not t else "mixed"


@dataclass
class Rule:
    pattern: str
    weight: int
    is_regex: bool = False
    source: str = "corpus"


def R(p, w, rx=False, source="corpus"):
    return Rule(p, w, rx, source)


KEYWORD_RULES: dict[str, list[Rule]] = {

    "Payment Method Inquiry": [
        R(r"\bkoko\b", 3, True),
        R(r"\binstallment", 3, True),
        R(r"\bcod\b", 2, True),
        R(r"\bcard", 3, True),
        R(r"\bpayment (method|plan|available|accept)", 3, True),
        R(r"\bbank transfer\b", 3, True),
        R(r"\bcash on delivery\b", 2, True),
        R("කොකො", 3),
        R(r"\bpay(ment)? .{0,12}(puluwanda|thiyanawada)", 2, True),
        R(r"\bkokoo\b", 3, True),
    ],


    "Price Inquiry": [
        R(r"\bmila\b", 3, True),
        R(r"\bkiyada\b", 2, True),
        R(r"\bkiyda\b", 2, True),
        R(r"\bkeeyda\b", 2, True),
        R(r"\bkeeyada\b", 2, True),
        R(r"\bkiyad\b", 3, True),
        R("කීයද", 2),
        R("කියද", 2),
        R("ගාන", 1),
        R(r"\bprize\b", 3, True),
        R(r"\bhow much\b", 2, True),
        R(r"\blist\b", 2, True),
        R(r"\bgana\b", 2, True),
        R(r"\bgaana\b", 1, True),
    ],

    
    "Location/Availability": [
        R(r"\bshowroom\b", 3, True),
        R(r"\blocation\b", 2, True),
        R(r"\bshop (eka|ekak)\b", 2, True),
        R(r"\bwhere .{0,10}(buy|get|shop)\b", 2, True),
        R(r"\bvisit (karala|karanna)\b", 2, True),
        R(r"\bawilla balala\b", 2, True),
        R(r"\bkohenda\b", 3, True),
        R(r"\bkohewath\b", 2, True),
        R(r"\bi'?m in \w+", 1, True),
        R(r"\bbranch\b", 2, True),
        R(r"\boutlet\b", 2, True),
        R("ශොප්", 2),
        R("ශෝරූම්", 3),
    ],

    "Delivery Inquiry": [
        R(r"\bdeliver\b", 2, True),
        R(r"\bdelivery\b", 1, True),
        R("ඩිලිවරි", 1),
        R(r"\b(?:delivery|deliver|shipping|courier)\s+(?:charges?|cost|fees?|kiyada|kohomada|available|thiyanawada|karanawada|karanwda)\b", 3, True),
        R(r"\bdawas kiy[ak]", 3, True),
        R(r"\bdws kiy", 3, True),
        R(r"\bcourier\b", 3, True),
        R(r"\b(karanawada|karanwda)", 1, True),
        R(r"\bhow (long|many days)\b", 2, True),
        R(r"\border eka dawas\b", 2, True),
        R("ගෙන්නන", 2),
        R(r"\bgenna ganne\b", 1, True),
        R(r"\bshipping\b", 1, True),
    ],

    "Purchase Intent": [
            R(r"\bneed\b", 2, True),
            R(r"\bwant\b", 2, True),
            R(r"\bganna\b", 1, True),
            R(r"\bgannawa\b", 2, True),
            R(r"\b(oni|one|ona|onee)\b", 2, True),
            R(r"\bekak\b", 1, True),
            R("මටත්", 3),
            R(r"(?<![\u0D80-\u0DFF])(ඕනේ|ඕනා|ඕනි|ඕන)(?![\u0D80-\u0DFF])", 2, True),
            R(r"\blooking for\b", 2, True),
            R(r"\bdenna\b", 1, True),
            R("ගන්න", 1),
            R(r"\bganna\b", 1, True),
            R(r"\bpuluwanda\b", 1, True),
        ],
    
    
    "Product Inquiry": [
            R(r"\bthiyanawada\b", 3, True),
            R(r"\bthiyenawada\b", 3, True),
            R(r"\bnedda\b", 3, True),
            R("විතරද", 3),
            R(r"\bwitharada\b", 2, True),
            R(r"\bganna barida\b", 3, True),
            R(r"\bmonawada\b", 2, True),
            R("මොනවද", 2),
            R("මොනවාද", 3),
            R(r"\bhow to use\b", 2, True),
            R(r"\bsafe (for|to)\b", 2, True),
            R(r"\bkohomada use\b", 2, True),
            R(r"\bkiyannako\b", 2, True),
            R(r"\bhodama .{0,12}(ekak|ekk|mkdd|mokadda)\b", 2, True),
        ],

    "Negative Feedback/Complaint": [
        R(r"\bganna? epa\b", 3, True),
        R("ගන්න එපා", 3),
        R("ගන්නෙපා", 3),
        R(r"\bgandepa\b", 3, True),
        R(r"\bdon'?t buy\b", 3, True),
        R(r"\bdonot buy\b", 2, True),
        R(r"\bdont take\b", 2, True),
        R(r"\bnot work", 3, True),
        R(r"\bwada n[aeh]", 2, True),
        R(r"\bwadak na", 2, True),
        R("වැඩ නෑ", 2),
        R("වැඩ කරන්නෙ නෑ", 2),
        R(r"\bkaduna\b", 2, True),
        R(r"\bdoesn'?t work\b", 2, True),
        R(r"\bstopped working\b", 2, True),
        R(r"\bwaste\b", 3, True),
        R(r"\bworst\b", 3, True),
        R(r"\bfake\b", 2, True),
        R(r"\bcheat", 2, True),
        R(r"\bfraud", 3, True),
        R(r"\bscam", 3, True),
        R("සවුත්තු", 2),
        R(r"\bsavuth", 2, True),
        R(r"\bsawuth", 2, True),
        R("බොරු", 2),
        R("රවට්ට", 2),
        R(r"\bdisappoint", 2, True),
        R(r"\bnot satisfied\b", 2, True),
        R(r"\bpoor quality\b", 3, True),
        R(r"\bnot good\b", 2, True),
        R(r"\bnot comfortable\b", 2, True),
        R(r"\bbad product\b", 3, True),
        R(r"\bnot quality\b", 2, True),
        R("පාඩුයි", 2),
        R("හිතුව තරම්", 2),
        R("කොලිටි නෑ", 2),
        R(r"\bwrong (item|product|colou?r|size|model)\b", 3, True),
        R("වැඩ කරන්නේ නැ", 2),
        R(r"\bmissing\b", 2, True),
        R(r"\bdamage", 2, True),
        R(r"\bbroken\b", 3, True),
        R(r"\b(wena|vena|different|wrong)\b", 2, True),
        R("වෙන එකක්", 2),
        R(r"\billapu\b.{0,30}\b(nemei|neme)\b", 2, True),
        R(r"ඉල්ලපු.{0,30}(නෙමෙයි|නෙමේ)", 2, True),
        R(r"\border? (eka )?thama n[ha]", 3, True),
        R(r"\banswer (karanne|krnne) na", 2, True),
        R(r"\bnot answering\b", 2, True),
        R(r"\breply karanne na", 2, True),
        R(r"\breact karanne n[ae]", 3, True),
        R(r"\bstill waiting\b", 3, True),
        R(r"\bnever received\b", 3, True),
    ],


    "Positive Feedback": [
        R(r"\bbest\b", 3, True),
        R(r"\bgood\b", 2, True),
        R(r"\bgreat\b", 3, True),
        R(r"\bsuper[bh]?\b", 3, True),
        R(r"\bexcellent\b", 3, True),
        R(r"\brecommend", 2, True),
        R(r"\breccomend", 2, True),
        R(r"\brecomend", 2, True),
        R(r"\brecommnd", 2, True),
        R(r"\bperfect\b", 3, True),
        R(r"\blove (it|this)\b", 3, True),
        R(r"\bnice\b", 1, True),
        R(r"\bwell done\b", 2, True),
        R(r"\bamazing\b", 2, True),
        R(r"\bawesome\b", 3, True),
        R(r"\bsupiri\b", 3, True),
        R(r"\bsuppa\b", 2, True),
        R(r"\bsupiriyak\b", 2, True),
        R(r"\bniyamai\b", 3, True),
        R(r"\bniyamyi\b", 2, True),
        R(r"\bpatta\b", 3, True),
        R(r"\bfatta\b", 3, True),
        R(r"\bmaru\b", 3, True),
        R(r"\bmaretama\b", 3, True),
        R(r"\bhodai\b", 3, True),
        R(r"\bhondai\b", 3, True),
        R(r"\bhodata\b", 2, True),
        R("හොදයි", 2),
        R("හොඳයි", 2),
        R("හොදම හොදයි", 2),
        R(r"(^|\s)හොද(\s|$|,|\.|!|\?)", 2, True),
        R("සුපිරි", 3),
        R("නියමයි", 2),
        R("පට්ට", 3),
        R("මරු", 3),
        R("ආදරෙයි", 2),
        R("ආදරේ", 3),
        R(r"\bcomfortable\b", 2, True),
        R(r"\bquality\b", 2, True),
        R(r"\bworth\b", 2, True),
        R(r"\bthanks?\b", 2, True),
        R(r"\bthank you\b", 3, True),
        R("ස්තූතියි", 3),
        R(r"\bvaluble\b", 3, True),
        R(r"\bvaluable\b", 3, True),
    ],


    "Noise/Off-topic": [
        R(r"\bfollow (kar|back|me)", 2, True),
        R("මාවත් follow", 2),
    ],

}


POSITIVE_EMOJI = set("❤️🥰😍💪👍🔥💯♥️💗🤍💫😎🩵😊🙂👌✨🎉🥳😁💖")
NEGATIVE_EMOJI = set("😡🤮😭😒🚫💔😤😠🙄😞😢")


def analyze_emoji(text: str) -> tuple[str, int, int]:
    pos = sum(1 for ch in text if ch in POSITIVE_EMOJI)
    neg = sum(1 for ch in text if ch in NEGATIVE_EMOJI)
    if pos > neg and pos > 0:
        return "Positive", pos, neg
    if neg > pos and neg > 0:
        return "Negative", pos, neg
    return "Neutral", pos, neg


_NEGATION_FILLER = r"(?:the|a|an|that|so|really|very|quite|too)\s+"
NEGATION_PATTERNS = [
    re.compile(r"(hodai|hondai|hoda|good|quality|comfortable)\s+(na+|n[ae]h|නෑ|නැ)", re.I),
    re.compile(r"(kisima|කිසිම)\s+(quality|hodak)?\s*(ekak)?\s*(na|නෑ)", re.I),
    re.compile(r"quality\s+ekak\s+na", re.I),
    re.compile(
        rf"\bnot\s+(?:{_NEGATION_FILLER})?"
        r"(good|great|nice|comfortable|working|worth|satisfied|recommended?|"
        r"best|excellent|amazing|perfect|quality)\b", re.I
    ),
    re.compile(r"(හොදයි|හොඳයි)\s*(නෑ|නැ)"),
    re.compile(r"don'?t\s+recommend", re.I),
]
QUESTION_FORM_PATTERNS = [
    re.compile(r"(hodai|hondai|hoda)(y|i)?da\b", re.I),
    re.compile(r"හොදයිද|හොඳයිද|හොඳද|හොදද"),
    re.compile(r"(supiri|niyamai|maru)da\b", re.I),

    re.compile(r"\b(?:is (?:this|it)|are (?:these|they))\s+(?:really\s+)?(?:good|safe|suitable|effective)\s+for\b", re.I),
    re.compile(r"\b(?:do|would) you recommend(?: this| it)?\b", re.I),
]

PRICE_WITHHELD_COMPLAINT_PATTERN = re.compile(
    r"(?:ගාන|මිල)\s*.{0,24}(?:කියන්න|කිය|දන්න).{0,12}"
    r"(?:නැත්තේ|නැහැ|නෑ|නැත|නැති)"
)

def is_quality_question(text: str) -> bool:
    return any(p.search(text) for p in QUESTION_FORM_PATTERNS)


def has_negated_positive(text: str) -> bool:
    return any(p.search(text) for p in NEGATION_PATTERNS)


@dataclass
class Classification:
    text: str
    language: str
    primary_intent: Optional[str]
    secondary_intent: Optional[str]
    confidence: str
    route: str
    ai_assisted: bool
    matched_keywords: dict = field(default_factory=dict)
    scores: dict = field(default_factory=dict)
    evidence_count: int = 0
    route_reason: str = ""


SCORE_THRESHOLD = 2
CLEAR_WINNER_MARGIN = 2


PRICE_REQUEST_PATTERNS = (

    re.compile(r"^\s*(?:price|prize|මිල|ගාන)\s*[?!.]*\s*$", re.I),
    re.compile(r"\b(?:price|prize)\b\s*(?:pl[sz]\b|please\b|kiyada\b|kiyda\b|\?)", re.I),
    re.compile(r"\b(?:what(?:'s| is)?\s+(?:the\s+)?price|tell\s+me\s+(?:the\s+)?price)\b", re.I),
    re.compile(r"\b(?:price|prize)\s+(?:of|for)\b.{0,45}\?", re.I),
    re.compile(r"(?:මිල|ගාන)\s*(?:කීයද|කියද|කියන්න|කීය|\?)"),
    re.compile(r"\b(?:gana|gaana)\s+(?:kiyada|kiyda|danna|kiyanna|kiyan|kiyanne)\b", re.I),
)



DETAIL_REQUEST_PATTERN = re.compile(
    r"\b(?:need|want)(?:\s+to)?(?:\s+more)?\s+"
    r"(?:details?|info(?:rmation)?|specs?|specifications?|features?)\b", re.I
)
DELIVERY_REQUEST_PATTERNS = (
    re.compile(
        r"\b(?:delivery|deliver|shipping|courier)\s+(?:charges?|cost|fees?|"
        r"kiyada|kohomada|available|thiyanawada|karanawada|karanwda)\b", re.I
    ),
    re.compile(r"\b(?:delivery|deliver|shipping|courier)\s+to\s+[a-z]+\b", re.I),
    re.compile(r"\b(?:do|can|could|will)\s+(?:you\s+)?(?:deliver|delivery|ship)\s+to\b", re.I),
    re.compile(r"\bhow\s+(?:long|many\s+days)\b.{0,35}\b(?:delivery|deliver|shipping)\b", re.I),
)
GENERIC_DELIVERY_PATTERNS = frozenset({
    r"\bdeliver\b", r"\bdelivery\b", r"\bshipping\b", r"\bcourier\b"
})
GENERIC_PRICE_PATTERNS = frozenset({
    r"\bkiyada\b", r"\bkiyda\b", r"\bkeeyda\b", r"\bkeeyada\b",
    r"\bkiyad\b", r"\bhow much\b", r"\bgana\b", r"\bgaana\b",
    "ගාන", "කීයද", "කියද"
})

def _matches_any(text: str, patterns: tuple) -> bool:
    return any(p.search(text) for p in patterns)


def _score_categories(norm_text: str) -> tuple[dict, dict]:
    scores: dict[str, int] = {}
    matches: dict[str, list[str]] = {}
    negated = has_negated_positive(norm_text)
    quality_question = is_quality_question(norm_text)
    details_request = bool(DETAIL_REQUEST_PATTERN.search(norm_text))
    delivery_request = _matches_any(norm_text, DELIVERY_REQUEST_PATTERNS)
    price_request = (_matches_any(norm_text, PRICE_REQUEST_PATTERNS)
                     and not PRICE_WITHHELD_COMPLAINT_PATTERN.search(norm_text))
    scoped_delivery_rule = any(
        r.is_regex and "(?:delivery|deliver|shipping|courier)" in r.pattern
        and re.search(r.pattern, norm_text)
        for r in KEYWORD_RULES.get("Delivery Inquiry", [])
    )

    for category, rules in KEYWORD_RULES.items():
        score = 0
        hit = []
        seen_exact = set()
        for rule in rules:

            key = (rule.pattern, rule.is_regex)
            if key in seen_exact:
                continue
            seen_exact.add(key)

            if category == "Purchase Intent" and details_request and rule.pattern in (
                r"\bneed\b", r"\bwant\b"
            ):
                continue


            if category == "Delivery Inquiry" and (scoped_delivery_rule or delivery_request) \
                    and rule.pattern in GENERIC_DELIVERY_PATTERNS:
                continue
            matched = (bool(re.search(rule.pattern, norm_text)) if rule.is_regex
                       else rule.pattern.lower() in norm_text)
            if matched:
                score += rule.weight
                hit.append(rule.pattern)


        if category == "Price Inquiry" and price_request:
            score = max(score, 3)
            hit.append("<price request context>")
        if category == "Delivery Inquiry" and delivery_request:
            score = max(score, 3)
            hit.append("<delivery request context>")
        if category == "Product Inquiry" and details_request:
            score = max(score, 3)
            hit.append("<details/information request context>")


        if category == "Positive Feedback" and negated:
            score, hit = 0, ["<suppressed: negated positive>"]
        if category == "Positive Feedback" and quality_question:
            score, hit = 0, ["<suppressed: quality question form>"]
        if score > 0:
            scores[category], matches[category] = score, hit


    combined_price_delivery = bool(re.search(
        r"\bhow\s+much\b.{0,90}\b(?:with|including|plus)\s+(?:the\s+)?delivery\b",
        norm_text, re.I
    ))
    if delivery_request and not price_request and not combined_price_delivery:
        price_hits = matches.get("Price Inquiry", [])
        if price_hits and all(h in GENERIC_PRICE_PATTERNS for h in price_hits):
            scores.pop("Price Inquiry", None)
            matches.pop("Price Inquiry", None)


    if quality_question:
        scores["Product Inquiry"] = max(scores.get("Product Inquiry", 0), 3)
        matches.setdefault("Product Inquiry", []).append("<quality question form>")
    if negated:
        scores["Negative Feedback/Complaint"] = scores.get("Negative Feedback/Complaint", 0) + 3
        matches.setdefault("Negative Feedback/Complaint", []).append("<negated positive>")
    return scores, matches


def classify(text: str) -> Classification:
    norm = normalize(text)
    lang = detect_language(norm)
    emoji_polarity, pos_e, neg_e = analyze_emoji(text)

    if lang == "emoji":
        if emoji_polarity == "Positive":
            ev = EVIDENCE.get(("Positive Feedback", "emoji"), 0)
            return Classification(
                text=text, language=lang,
                primary_intent="Positive Feedback", secondary_intent=None,
                confidence="high" if ev >= EVIDENCE_HIGH else "medium",
                route="rules_only" if ev >= EVIDENCE_HIGH else "rules_ai_verify",
                ai_assisted=ev < EVIDENCE_HIGH,
                matched_keywords={"Positive Feedback": [f"emoji x{pos_e}"]},
                evidence_count=ev,
                route_reason=f"Emoji-only positive ({pos_e} positive emoji); evidence={ev}",
            )
        if emoji_polarity == "Negative":
            return Classification(
                text=text, language=lang,
                primary_intent="Negative Feedback/Complaint", secondary_intent=None,
                confidence="medium", route="rules_ai_verify", ai_assisted=True,
                matched_keywords={"Negative Feedback/Complaint": [f"emoji x{neg_e}"]},
                evidence_count=0,
                route_reason="Emoji-only negative — no corpus evidence for this cell; AI verifies",
            )
        return Classification(
            text=text, language=lang, primary_intent=None, secondary_intent=None,
            confidence="none", route="ai_only",
            ai_assisted=True, route_reason="Emoji/non-text with no polarity signal",
        )

    if contains_mobile_number(norm):
        return Classification(
            text=text,
            language=lang,
            primary_intent=None,
            secondary_intent=None,
            confidence="none",
            route="ai_only",
            ai_assisted=True,
            matched_keywords={"Order/Purchase Confirmation": ["<mobile number detected>"]},
            scores={},
            evidence_count=0,
            route_reason=(
                "Mobile number detected; AI must determine whether the complete "
                "comment contains name + mobile number + delivery address as an "
                "Order/Purchase Confirmation."
            ),
        )

    ai_only_guard = detect_ai_only_risk(norm)
    if ai_only_guard is not None:
        return Classification(
            text=text, language=lang,
            primary_intent=None, secondary_intent=None,
            confidence="none", route="ai_only", ai_assisted=True,
            matched_keywords={}, scores={}, evidence_count=0,
            route_reason=ai_only_guard.reason,
        )

    scores, matches = _score_categories(norm)
    if not scores:
        return Classification(
            text=text, language=lang, primary_intent=None, secondary_intent=None,
            confidence="none", route="ai_only", ai_assisted=True, scores={},
            route_reason="No keyword rule matched — outside rule vocabulary coverage",
        )

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    primary, primary_score = ranked[0]
    secondary = None
    if len(ranked) > 1 and ranked[1][1] >= SCORE_THRESHOLD:
        secondary = ranked[1][0]

    if primary_score < SCORE_THRESHOLD:
        return Classification(
            text=text, language=lang, primary_intent=primary, secondary_intent=None,
            confidence="none", route="ai_only", ai_assisted=True,
            matched_keywords=matches, scores=scores,
            route_reason=f"Keyword score {primary_score} below threshold {SCORE_THRESHOLD}",
        )

    if (len(ranked) > 1 and (primary_score - ranked[1][1]) < CLEAR_WINNER_MARGIN
            and ranked[1][1] >= SCORE_THRESHOLD):
        ev = EVIDENCE.get((primary, lang), 0)
        return Classification(
            text=text, language=lang, primary_intent=primary,
            secondary_intent=ranked[1][0],
            confidence="medium", route="rules_ai_verify", ai_assisted=True,
            matched_keywords=matches, scores=scores, evidence_count=ev,
            route_reason=(f"Ambiguous: '{primary}' ({primary_score}) vs "
                          f"'{ranked[1][0]}' ({ranked[1][1]}) within margin — AI verifies"),
        )

    evidence = EVIDENCE.get((primary, lang), 0)
    if evidence >= EVIDENCE_HIGH:
        route, conf, ai = "rules_only", "high", False
        reason = (f"Rule match with {evidence} corpus examples for "
                  f"({primary}, {lang}) — evidence >= {EVIDENCE_HIGH}")
    elif evidence >= EVIDENCE_LOW:
        route, conf, ai = "rules_ai_verify", "medium", True
        reason = (f"Rule matched but only {evidence} corpus examples for "
                  f"({primary}, {lang}) — below high-evidence threshold; AI verifies")
    else:
        route, conf, ai = "ai_only", "none", True
        reason = (f"Only {evidence} corpus examples for ({primary}, {lang}) — "
                  f"insufficient evidence to trust a rule in this language; AI classifies")

    return Classification(
        text=text, language=lang, primary_intent=primary,
        secondary_intent=secondary,
        confidence=conf, route=route, ai_assisted=ai,
        matched_keywords=matches, scores=scores, evidence_count=evidence,
        route_reason=reason,
    )
