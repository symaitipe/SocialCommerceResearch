"""
Hybrid Comment Classification Rule Engine
==========================================
Sri Lankan Facebook Social Commerce — English / Sinhala / Singlish / Mixed

Architecture:
  Layer 1 (this module): rule-based classification with evidence-based
           per-language confidence derived from the annotated corpus.
  Layer 2 (AI fallback): comments this engine cannot classify with
           sufficient evidence-backed confidence are routed to the LLM.

Every decision is explainable: the output includes which keywords fired,
the evidence count behind the (category, language) cell, and the exact
reason a comment was routed to AI.

Evidence matrix source: Corpus A (536 comments, 5 verticals, sequential
collection) + Corpus B (52 targeted complaint/negative examples).
Total: 588 annotated comments.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional
from app.rules.routing_guards import (
    detect_ai_only_risk,
    needs_confirmation_context_review,
)

# ═══════════════════════════════════════════════════════════════════════════
# 1. EVIDENCE MATRIX  (real counts from the annotated corpus — do not invent)
#    evidence[(category, language)] = number of annotated examples
# ═══════════════════════════════════════════════════════════════════════════

EVIDENCE: dict[tuple[str, str], int] = {
    # Positive Feedback
    ("Positive Feedback", "english"): 102,
    ("Positive Feedback", "singlish"): 48,
    ("Positive Feedback", "sinhala"): 41,
    ("Positive Feedback", "mixed"): 24,
    ("Positive Feedback", "emoji"): 7,
    # Product Inquiry
    ("Product Inquiry", "english"): 29,
    ("Product Inquiry", "singlish"): 35,
    ("Product Inquiry", "sinhala"): 12,
    ("Product Inquiry", "mixed"): 9,
    # Purchase Intent
    ("Purchase Intent", "english"): 15,
    ("Purchase Intent", "singlish"): 18,
    ("Purchase Intent", "sinhala"): 20,
    ("Purchase Intent", "mixed"): 1,
    # Price Inquiry
    ("Price Inquiry", "english"): 13,
    ("Price Inquiry", "singlish"): 26,
    ("Price Inquiry", "sinhala"): 12,
    ("Price Inquiry", "mixed"): 1,
    # Delivery Inquiry
    ("Delivery Inquiry", "english"): 5,
    ("Delivery Inquiry", "singlish"): 15,
    ("Delivery Inquiry", "sinhala"): 4,
    ("Delivery Inquiry", "mixed"): 4,
    # Negative Feedback/Complaint  (Corpus A + Corpus B)
    ("Negative Feedback/Complaint", "english"): 30,
    ("Negative Feedback/Complaint", "singlish"): 14,
    ("Negative Feedback/Complaint", "sinhala"): 12,
    ("Negative Feedback/Complaint", "mixed"): 8,
    # Order/Purchase Confirmation
    ("Order/Purchase Confirmation", "english"): 9,
    ("Order/Purchase Confirmation", "singlish"): 7,
    ("Order/Purchase Confirmation", "sinhala"): 2,
    ("Order/Purchase Confirmation", "mixed"): 3,
    # Location/Availability
    ("Location/Availability", "english"): 9,
    ("Location/Availability", "singlish"): 7,
    ("Location/Availability", "sinhala"): 0,
    ("Location/Availability", "mixed"): 0,
    # Payment Method Inquiry
    ("Payment Method Inquiry", "english"): 5,
    ("Payment Method Inquiry", "singlish"): 9,
    ("Payment Method Inquiry", "sinhala"): 1,
    ("Payment Method Inquiry", "mixed"): 0,
    # Noise/Off-topic
    ("Noise/Off-topic", "english"): 7,
    ("Noise/Off-topic", "singlish"): 4,
    ("Noise/Off-topic", "sinhala"): 1,
    ("Noise/Off-topic", "mixed"): 2,
    ("Noise/Off-topic", "emoji"): 1,
}

# Evidence thresholds → routing policy
EVIDENCE_HIGH = 5    # >= 5 examples: rule decision stands on its own
EVIDENCE_LOW = 3     # 3-4 examples: rule fires but AI verifies
                     # < 3 examples: no rule trust — AI classifies directly

# Categories the rule engine NEVER claims — always AI (insufficient corpus
# evidence in every language mode: <= 5 total examples each)
AI_ONLY_CATEGORIES = frozenset({
    "Warranty/Service Inquiry",
    "Contact Request",
    "Price Complaint",
    "Suggestion",
})

RULE_CATEGORIES = [
    "Purchase Intent", "Product Inquiry", "Price Inquiry", "Delivery Inquiry",
    "Location/Availability", "Payment Method Inquiry",
    "Order/Purchase Confirmation", "Positive Feedback",
    "Negative Feedback/Complaint", "Noise/Off-topic",
]

# ═══════════════════════════════════════════════════════════════════════════
# 2. TEXT NORMALISATION
# ═══════════════════════════════════════════════════════════════════════════

def normalize(text: str) -> str:
    """NFC-normalise (Sinhala has NFC/NFD variants in the wild) and
    lowercase the Latin portion. Sinhala has no case so lower() is safe."""
    if text is None:
        return ""
    t = unicodedata.normalize("NFC", str(text))
    return t.lower().strip()

SINHALA_RANGE = re.compile(r"[\u0D80-\u0DFF]")
LATIN_RANGE = re.compile(r"[a-zA-Z]")
EMOJI_RANGE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF\u2764\ufe0f]"
)

# ═══════════════════════════════════════════════════════════════════════════
# 3. LANGUAGE DETECTION
#    Script-range first (deterministic), Singlish lexicon second.
#    Approach per Barman et al. (2014): script detection as primary signal.
# ═══════════════════════════════════════════════════════════════════════════

# High-frequency Singlish tokens observed in the corpus. These are romanised
# Sinhala words that do not exist in English — presence of ANY marks the
# Latin text as Singlish rather than English.
SINGLISH_MARKERS = {
    # price / money
    "kiyada", "kiyda", "keeyda", "kohomada", "kohomda", "kohmada", "gana",
    "gaana", "ganata", "mila", "salli", "keeyada", "kiyad",
    # want / need / buy
    "oni", "one", "ona", "onee", "ganna", "gannawa", "aragena", "gatta",
    "gaththa", "genna", "matath", "mata", "mama", "mage", "denna",
    # availability / existence
    "thiyanawada", "tiyenawada", "thiyenawada", "thibeda", "thiyeda",
    "nedda", "ndda", "nadda", "naa", "nane", "nhane", "athi", "tyenne",
    "thinne", "tiyenne", "thiyanawa", "tiyenawa",
    # good / bad
    "hodai", "hondai", "hodata", "hoda", "niyamai", "supiri", "suppa",
    "patta", "maru", "maretama", "marama", "awl", "awlk", "aulak",
    "savuththu", "sawuththu", "wada", "vada", "wadak", "kaduna",
    # delivery / order
    "dawas", "dws", "ewanna", "ewnwd", "hambune", "hambuna", "hamben",
    "aawa", "awa", "awilla", "enne", "yanawa", "ynwd", "damma", "demma",
    "kara", "kala", "karanne", "karanna", "krnne", "puluwanda", "puluwnda",
    "barida", "berida", "epa", "meka", "meeka", "ekak", "ekk", "eka",
    # misc high-frequency
    "machan", "machang", "bro", "aiye", "bn", "ban", "wage", "witharada",
    "witharai", "kenek", "kenkt", "monawada", "mkdd", "mokadda",
}

def detect_language(text: str) -> str:
    """Returns one of: english, sinhala, singlish, mixed, emoji"""
    t = normalize(text)
    has_sinhala = bool(SINHALA_RANGE.search(t))
    has_latin = bool(LATIN_RANGE.search(t))
    has_emoji = bool(EMOJI_RANGE.search(t))

    if has_sinhala and has_latin:
        return "mixed"
    if has_sinhala:
        return "sinhala"
    if has_latin:
        # Latin script: English or Singlish? Lexicon lookup on word tokens.
        tokens = set(re.findall(r"[a-z]+", t))
        if tokens & SINGLISH_MARKERS:
            return "singlish"
        return "english"
    if has_emoji:
        return "emoji"
    return "emoji" if not t else "mixed"  # digits/punct-only → treat as emoji/non-text

# ═══════════════════════════════════════════════════════════════════════════
# 4. KEYWORD RULES
#    Every keyword below was observed in the annotated corpus. Each rule is
#    (pattern, weight). Weight reflects specificity:
#      3 = unambiguous, category-defining ("koko", "kiyada", "ganna epa")
#      2 = strong signal, rare collisions
#      1 = supporting signal, needs company or wins only unopposed
#    Patterns are matched on normalised text. \b works for Latin;
#    Sinhala patterns use plain substring (no word boundaries in script).
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Rule:
    pattern: str
    weight: int
    is_regex: bool = False

def R(p, w, rx=False):
    return Rule(p, w, rx)

KEYWORD_RULES: dict[str, list[Rule]] = {

    # ── NEGATIVE FEEDBACK / COMPLAINT ─────────────────────────────────────
    # Checked FIRST because negation patterns override positive/intent words
    # ("ganna epa" must beat "ganna"; "wada na" must beat "wada niyamai")
    "Negative Feedback/Complaint": [
        # don't-buy warnings (Sinhala + Singlish + English)
        R(r"\bganna? epa\b", 3, True), R("ගන්න එපා", 3), R("ගන්නෙපා", 3),
        R(r"\bgandepa\b", 3, True), R(r"\bdon'?t buy\b", 3, True),
        R(r"\bdonot buy\b", 3, True), R(r"\bdont take\b", 3, True),
        R("කවුරුවත් ගන්න", 3), R("කිසිම කෙනෙක් ගන්න", 3),
        # not working / broken
        R(r"\bnot work", 3, True), R(r"\bwada n[aeh]", 3, True),
        R(r"\bvada n[aeh]", 3, True), R(r"\bwadak na", 3, True),
        R("වැඩ නෑ", 3), R("වැඩ කරන්නෙ නෑ", 3), R("වැඩ කරන්නේ නැ", 3),
        R(r"\bkaduna\b", 3, True), R(r"\bnot charging\b", 3, True),
        R(r"\bdoesn'?t work\b", 3, True), R(r"\bstopped working\b", 3, True),
        # waste / worst / fake / cheating
        R(r"\bwaste\b", 3, True), R(r"\bworst\b", 3, True),
        R(r"\bfake\b", 3, True), R(r"\bcheat", 3, True), R(r"\bfraud", 3, True),
        R(r"\bscam", 3, True), R("සවුත්තු", 3), R(r"\bsavuth", 3, True),
        R(r"\bsawuth", 3, True), R("බොරු", 3), R("රවට්ට", 3),
        # disappointment / quality complaints
        R(r"\bdisappoint", 3, True), R(r"\bnot satisfied\b", 3, True),
        R(r"\bpoor quality\b", 3, True), R(r"\bnot good\b", 2, True),
        R(r"\bnot comfortable\b", 2, True), R(r"\bbad product", 3, True),
        R(r"\bnot quality\b", 2, True), R("පාඩුයි", 3),
        R("හිතුව තරම් කොලිටි නෑ", 3), R("කොලිටි නෑ", 3),
        # wrong item / missing / damaged
        R(r"\bwrong colou?r\b", 3, True), R(r"\bmissing\b", 2, True),
        R(r"\bdamage", 2, True), R(r"\bbroken\b", 3, True),
        R("වෙන ekak", 2), R("wena ekak", 2), R("කලූ", 1), R("කලුනේ අවේ", 3),
        R(r"\billapu pata neme\b", 3, True),
        # order not arrived / seller not responding (complaint form)
        R(r"\border? (eka )?thama n[ha]", 3, True),
        R(r"\banswer (karanne|krnne) na", 3, True),
        R(r"\bnot answering\b", 3, True), R(r"\breply karanne na", 3, True),
        R(r"\breact karanne n[ae]", 3, True),
        R("එකයි ඇවිත්", 2), R(r"\bstill waiting\b", 3, True),
        R(r"\bnever received\b", 3, True),
        R(r"\bahenne? na", 2, True), R("ඇහෙන්නෙ නෑ", 3), R("ඇහෙන්නේ", 1),
        R(r"\b(one|1) side not working\b", 3, True),
        R(r"\bahenawa adui\b", 3, True), R("බැලන්ස් නෑ", 3),
        R(r"\bepa\b", 1, True), R("එපා", 1),
    ],

    # ── PAYMENT METHOD INQUIRY ────────────────────────────────────────────
    # "koko" is the single most specific token in the whole corpus
    "Payment Method Inquiry": [
        R(r"\bkoko\b", 3, True), R(r"\binstallment", 3, True),
        R(r"\bcard payment", 3, True), R(r"\bcard eken\b", 3, True),
        R(r"\bpayment (method|plan|available|accept)", 3, True),
        R(r"\bbank transfer\b", 3, True), R(r"\bcash on delivery\b", 2, True),
        R(r"\bpay(ment)? .{0,12}(available|accept|puluwanda|thiyanawada)", 2, True),
    ],

    # ── PRICE INQUIRY ─────────────────────────────────────────────────────
    "Price Inquiry": [
        R(r"\bmila kiyada\b", 3, True), R(r"\bkiyada\b", 3, True),
        R(r"\bkiyda\b", 3, True), R(r"\bkeeyda\b", 3, True),
        R(r"\bkeeyada\b", 3, True), R(r"\bkiyad\b", 3, True),
        R("කීයද", 3), R("කියද", 3), R("මිල", 2), R("ගාන", 2), R("ගණන", 1),
        R(r"\bprice\b", 3, True), R(r"\bprize\b", 3, True),  # common misspelling
        R(r"\bhow much\b", 3, True), R(r"\bprice list\b", 3, True),
        R(r"\bgana danna\b", 3, True), R(r"\bgaana\b", 2, True),
        R(r"\bfull price\b", 3, True),
    ],

    # ── DELIVERY INQUIRY ──────────────────────────────────────────────────
    "Delivery Inquiry": [
        R(r"\bdelivery (charge|cost|fee|kiyada|kohomada)", 3, True),
        R(r"\bdawas kiy[ak]", 3, True), R(r"\bdws kiy", 3, True),
        R(r"\bcod\b", 3, True), R(r"\bcourier\b", 3, True),
        R(r"\bdelivery (thiyanawada|available|karanawada|karanwda)", 3, True),
        R(r"\bhow (long|many days)\b", 2, True),
        R(r"\border eka dawas\b", 3, True),
        R("ඩිලිවරි", 2), R("ගෙන්නන", 2), R(r"\bgenna ganne\b", 2, True),
        R(r"\bdeliver\b", 2, True), R(r"\bdelivery\b", 1, True),
        R(r"\bshipping\b", 1, True),
        R(r"\bweekend .{0,15}orders?\b", 2, True),
        R(r"\borders? ewnw", 2, True),
    ],

    # ── LOCATION / AVAILABILITY ───────────────────────────────────────────
    "Location/Availability": [
        R(r"\bshowroom\b", 3, True), R(r"\bshop location\b", 3, True),
        R(r"\bshop (eka|ekak)\b", 3, True),
        R(r"\bwhere can i buy\b", 3, True), R(r"\bwhere .{0,10}(buy|get|shop)\b", 2, True),
        R(r"\bvisit (karala|karanna)\b", 3, True),
        R(r"\bawilla balala\b", 3, True),
        R(r"\bkohenda\b", 3, True), R(r"\bkohewath\b", 2, True),
        R(r"\bi'?m in \w+", 2, True),  # "I need I'm in Welimada"
        R(r"\bbranch\b", 2, True), R(r"\boutlet\b", 2, True),
        R("ශොප්", 2), R("ශෝරූම්", 3),
    ],

    # ── ORDER / PURCHASE CONFIRMATION ─────────────────────────────────────
    "Order/Purchase Confirmation": [
        R(r"\border (kara|kala|kla)\b", 3, True),
        R(r"\bo[rd]der ek[ka]+ (damma|demma|dunna)\b", 3, True),
        R(r"\boder ekk damma\b", 3, True),
        R("ඕඩර් කරා", 3), R("ඕඩර් කලා", 3), R("ඔඩර් කරා", 3),
        R(r"\bgot mine\b", 3, True), R(r"\bi got my\b", 3, True),
        R(r"\breceived (my|the|today)\b", 3, True),
        R(r"\bhambun[ea]\b", 3, True), R(r"\bhambuna\b", 3, True),
        R(r"\bgatta\b", 2, True), R(r"\bgaththa\b", 2, True),
        R(r"\bmath gatta\b", 3, True),
        R("අද අවා", 3), R("ඇවිත්", 1), R(r"\baragena\b", 2, True),
        R(r"\bordered\b", 2, True), R(r"\border (kalaa?|krla)\b", 2, True),
        R(r"\bmamath .{0,6}gatha\b", 3, True),
    ],

    # ── PURCHASE INTENT ───────────────────────────────────────────────────
    "Purchase Intent": [
        R(r"\bmatath (oni|one|ona)\b", 3, True),
        R(r"\bmata (oni|one|ona|onee)\b", 3, True),
        R("මටත් ඕනේ", 3), R("මටත් ඕනා", 3), R("මටත් ඕන", 3), R("මටත් ඕනි", 3),
        R("මටත් එකක්", 3), R("ඕනි", 2), R("ඕනේ", 2), R("ඕන", 1),
        R(r"\bi need (one|it|this)\b", 3, True), R(r"\bi need\b", 2, True),
        R(r"\bi want (one|it|this)\b", 3, True),
        R(r"\bganna (one|oni|ona)\b", 3, True),
        R(r"\bgannawa\b", 2, True), R(r"\bgannawamai\b", 3, True),
        R(r"\baniwaren .{0,8}gannawa\b", 3, True),
        R(r"\blooking for\b", 2, True),
        R(r"\bekk oni\b", 3, True), R(r"\bekak oni\b", 3, True),
        R(r"\b\d+\s?ml denna\b", 3, True), R(r"\bdenna\b", 1, True),
        R(r"\benne .{0,8}order\b", 2, True),
        R("ගන්න hadanne", 3), R(r"\bganna hadanne\b", 3, True),
        R(r"\beka (oni|one)\b", 2, True),
    ],

    # ── PRODUCT INQUIRY ───────────────────────────────────────────────────
    "Product Inquiry": [
        # availability-of-variant questions
        R(r"\bthiyanawada\b", 3, True), R(r"\btiyenawada\b", 3, True),
        R(r"\bthiyenawada\b", 3, True), R(r"\bthibeda\b", 3, True),
        R(r"\bthiyeda\b", 3, True), R(r"\bnedda\b", 3, True),
        R(r"\bndda\b", 3, True), R(r"\bnadda\b", 3, True),
        R("තියෙනවද", 3), R("තියෙනවාද", 3), R("තිබේද", 3), R("තියෙද", 3),
        R("විතරද", 2), R(r"\bwitharada\b", 3, True),
        # can-I-get questions
        R(r"\bganna puluwanda\b", 2, True), R(r"\bganna puluwnda\b", 2, True),
        R(r"\bganna barida\b", 2, True), R(r"\bganna berida\b", 2, True),
        R(r"\bcan (i|we) (get|purchase|buy)\b", 2, True),
        R("ගන්න පුළුවන්ද", 2), R("ගන්න බැරිද", 2),
        # product attribute questions
        R(r"\bunisex\b", 2, True), R(r"\bladies (ewa|perform|perfume)\b", 2, True),
        R(r"\bmonawada\b", 2, True), R("මොනවද", 2), R("මොනවාද", 2),
        R(r"\blongevity\b", 3, True), R(r"\bsize\b", 1, True),
        R(r"\bcolou?rs?\b", 1, True), R(r"\bhow to (use|get|buy|order)\b", 2, True),
        R(r"\bis it ok to use\b", 3, True), R(r"\bsafe (for|to)\b", 2, True),
        R("පාවිච්චි", 2), R(r"\bpawichchi\b", 2, True),
        R(r"\bkohomada (ganne|use|order)\b", 2, True),
        R(r"\b\d+\s?ml\b", 1, True),
        R(r"\bfull bottle\b", 1, True), R(r"\bdecant\b", 2, True),
        R(r"\bavailable\b", 1, True),
        R(r"\bkiyannako\b", 2, True),  # "recommend me one" requests
        R(r"\bhodama .{0,12}(ekak|ekk|mkdd|mokadda)\b", 2, True),
    ],

    # ── POSITIVE FEEDBACK ─────────────────────────────────────────────────
    "Positive Feedback": [
        R(r"\bbest\b", 2, True), R(r"\bgood\b", 2, True), R(r"\bgreat\b", 2, True),
        R(r"\bsuper[bh]?\b", 2, True), R(r"\bexcellent\b", 3, True),
        R(r"\brecommend", 3, True), R(r"\breccomend", 3, True),
        R(r"\brecomend", 3, True), R(r"\brecommnd", 3, True),
        R(r"\bperfect\b", 3, True), R(r"\blove (it|this)\b", 3, True),
        R(r"\bnice\b", 2, True), R(r"\bwell done\b", 3, True),
        R(r"\bamazing\b", 3, True), R(r"\bawesome\b", 3, True),
        R(r"\bsupiri\b", 3, True), R(r"\bsuppa\b", 3, True),
        R(r"\bsupiriyak\b", 3, True), R(r"\bniyamai\b", 3, True),
        R(r"\bniyamyi\b", 3, True), R(r"\bpatta\b", 3, True),
        R(r"\bfatta\b", 3, True), R(r"\bmaru\b", 2, True),
        R(r"\bmaretama\b", 3, True), R(r"\bhodai\b", 2, True),
        R(r"\bhondai\b", 2, True), R(r"\bhodata\b", 2, True),
        R("හොදයි", 2), R("හොඳයි", 2), R("හොදම හොදයි", 3), R("හොදටම", 3),
        R("සුපිරි", 3), R("නියමයි", 3), R("පට්ට", 3), R("මරු", 2),
        R("ආදරෙයි", 3), R("ආදරේ", 2),
        R(r"\bcomfortable\b", 2, True), R(r"\bquality\b", 1, True),
        R(r"\bworth\b", 2, True), R(r"\bthanks?\b", 2, True),
        R(r"\bthank you\b", 2, True), R("ස්තූතියි", 3),
        R(r"\bgrown\b", 1, True), R(r"\bvaluble\b", 2, True),
        R(r"\bvaluable\b", 2, True),
    ],

    # ── NOISE / OFF-TOPIC ─────────────────────────────────────────────────
    "Noise/Off-topic": [
        R(r"\bfollow (kar|back|me)", 3, True), R("මාවත් follow", 3),
        R(r"\blike ekakuth\b", 3, True),
        R(r"^\s*$", 3, True),  # empty
        R(r"^nan$", 3, True),  # null artefacts
    ],
}

# ═══════════════════════════════════════════════════════════════════════════
# 5. EMOJI ANALYSER  (supplementary signal — Liu et al. 2021 support)
# ═══════════════════════════════════════════════════════════════════════════

POSITIVE_EMOJI = set("❤️🥰😍💪👍🔥💯♥️💗🤍💫😎🩵😊🙂👌✨🎉🥳😁💖")
NEGATIVE_EMOJI = set("😡🤮😭😒🚫💔😤😠🙄😞😢")

def analyze_emoji(text: str) -> tuple[str, int, int]:
    """Returns (polarity, positive_count, negative_count)."""
    pos = sum(1 for ch in text if ch in POSITIVE_EMOJI)
    neg = sum(1 for ch in text if ch in NEGATIVE_EMOJI)
    if pos > neg and pos > 0:
        return "Positive", pos, neg
    if neg > pos and neg > 0:
        return "Negative", pos, neg
    return "Neutral", pos, neg

# ═══════════════════════════════════════════════════════════════════════════
# 6. NEGATION GUARD
#    Positive keywords immediately followed/preceded by negators must not
#    count as positive. Observed corpus patterns: "hoda na", "wada na",
#    "quality ekak na", "hodai na".
# ═══════════════════════════════════════════════════════════════════════════

NEGATION_PATTERNS = [
    re.compile(r"(hodai|hondai|hoda|good|quality|comfortable)\s+(na+|n[ae]h|නෑ|නැ)", re.I),
    re.compile(r"(kisima|කිසිම)\s+(quality|hodak)?\s*(ekak)?\s*(na|නෑ)", re.I),
    re.compile(r"quality\s+ekak\s+na", re.I),
    re.compile(r"not\s+(good|great|nice|comfortable|working|worth|satisfied|recommended?)", re.I),
    re.compile(r"(හොදයි|හොඳයි)\s*(නෑ|නැ)"),
    re.compile(r"don'?t\s+recommend", re.I),
]

# Question-form guard: "hodai + da" = "is it good?" — an inquiry, not praise.
# The Sinhala/Singlish interrogative particle "da/ද" flips feedback→inquiry.
QUESTION_FORM_PATTERNS = [
    re.compile(r"(hodai|hondai|hoda)(y|i)?da\b", re.I),
    re.compile(r"හොදයිද|හොඳයිද|හොඳද|හොදද"),
    re.compile(r"(supiri|niyamai|maru)da\b", re.I),
]

def is_quality_question(text: str) -> bool:
    return any(p.search(text) for p in QUESTION_FORM_PATTERNS)

def has_negated_positive(text: str) -> bool:
    return any(p.search(text) for p in NEGATION_PATTERNS)

# ═══════════════════════════════════════════════════════════════════════════
# 7. SENTIMENT (rule layer)
# ═══════════════════════════════════════════════════════════════════════════

INTENT_DEFAULT_SENTIMENT = {
    "Positive Feedback": "Positive",
    "Negative Feedback/Complaint": "Negative",
    "Purchase Intent": "Neutral",
    "Product Inquiry": "Neutral",
    "Price Inquiry": "Neutral",
    "Delivery Inquiry": "Neutral",
    "Location/Availability": "Neutral",
    "Payment Method Inquiry": "Neutral",
    "Order/Purchase Confirmation": "Neutral",
    "Noise/Off-topic": "Neutral",
}

# ═══════════════════════════════════════════════════════════════════════════
# 8. CLASSIFICATION RESULT
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Classification:
    text: str
    language: str
    primary_intent: Optional[str]
    secondary_intent: Optional[str]
    sentiment: str
    confidence: str                # "high" | "medium" | "none"
    route: str                     # "rules_only" | "rules_ai_verify" | "ai_only"
    ai_assisted: bool
    matched_keywords: dict = field(default_factory=dict)  # category -> [patterns]
    scores: dict = field(default_factory=dict)
    evidence_count: int = 0
    route_reason: str = ""
    priority_score: int = 0

# ═══════════════════════════════════════════════════════════════════════════
# 9. THE CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════

# Minimum keyword score for a category to be considered "matched"
SCORE_THRESHOLD = 2
# Margin by which the winner must beat the runner-up to be unambiguous
CLEAR_WINNER_MARGIN = 2

# Dashboard priority weights (higher = surfaced first)
PRIORITY_WEIGHTS = {
    "Negative Feedback/Complaint": 100,
    "Purchase Intent": 90,
    "Warranty/Service Inquiry": 80,
    "Contact Request": 75,
    "Price Complaint": 70,
    "Payment Method Inquiry": 60,
    "Price Inquiry": 55,
    "Delivery Inquiry": 50,
    "Product Inquiry": 45,
    "Location/Availability": 40,
    "Order/Purchase Confirmation": 35,
    "Suggestion": 30,
    "Positive Feedback": 10,
    "Noise/Off-topic": 0,
}

def _score_categories(norm_text: str) -> tuple[dict, dict]:
    """Score every rule category against the text. Returns (scores, matches)."""
    scores: dict[str, int] = {}
    matches: dict[str, list[str]] = {}
    negated = has_negated_positive(norm_text)

    for category, rules in KEYWORD_RULES.items():
        s = 0
        hit = []
        for rule in rules:
            if rule.is_regex:
                if re.search(rule.pattern, norm_text):
                    s += rule.weight
                    hit.append(rule.pattern)
            else:
                if rule.pattern.lower() in norm_text:
                    s += rule.weight
                    hit.append(rule.pattern)
        # Negation guard: suppress Positive Feedback if positives are negated
        if category == "Positive Feedback" and negated:
            s = 0
            hit = ["<suppressed: negated positive>"]
        # Question-form guard: "hodaida?" is an inquiry about quality, not praise
        if category == "Positive Feedback" and is_quality_question(norm_text):
            s = 0
            hit = ["<suppressed: quality question form>"]
        if s > 0:
            scores[category] = s
            matches[category] = hit

    # Question-form bonus: quality questions are Product Inquiry
    if is_quality_question(norm_text):
        scores["Product Inquiry"] = scores.get("Product Inquiry", 0) + 3
        matches.setdefault("Product Inquiry", []).append("<quality question form>")
    # Negated positives are complaints
    if negated:
        scores["Negative Feedback/Complaint"] = scores.get("Negative Feedback/Complaint", 0) + 3
        matches.setdefault("Negative Feedback/Complaint", []).append("<negated positive>")
    return scores, matches


def classify(text: str) -> Classification:
    """Full hybrid layer-1 classification with evidence-based routing."""
    norm = normalize(text)
    lang = detect_language(norm)
    emoji_polarity, pos_e, neg_e = analyze_emoji(text)

    # ---- Emoji-only comments ------------------------------------------------
    if lang == "emoji":
        if emoji_polarity == "Positive":
            ev = EVIDENCE.get(("Positive Feedback", "emoji"), 0)
            return Classification(
                text=text, language=lang,
                primary_intent="Positive Feedback", secondary_intent=None,
                sentiment="Positive", confidence="high" if ev >= EVIDENCE_HIGH else "medium",
                route="rules_only" if ev >= EVIDENCE_HIGH else "rules_ai_verify",
                ai_assisted=ev < EVIDENCE_HIGH,
                matched_keywords={"Positive Feedback": [f"emoji x{pos_e}"]},
                evidence_count=ev,
                route_reason=f"Emoji-only positive ({pos_e} positive emoji); evidence={ev}",
                priority_score=PRIORITY_WEIGHTS["Positive Feedback"],
            )
        if emoji_polarity == "Negative":
            return Classification(
                text=text, language=lang,
                primary_intent="Negative Feedback/Complaint", secondary_intent=None,
                sentiment="Negative", confidence="medium",
                route="rules_ai_verify", ai_assisted=True,
                matched_keywords={"Negative Feedback/Complaint": [f"emoji x{neg_e}"]},
                evidence_count=0,
                route_reason="Emoji-only negative — no corpus evidence for this cell; AI verifies",
                priority_score=PRIORITY_WEIGHTS["Negative Feedback/Complaint"],
            )
        return Classification(
            text=text, language=lang, primary_intent=None, secondary_intent=None,
            sentiment="Neutral", confidence="none", route="ai_only",
            ai_assisted=True, route_reason="Emoji/non-text with no polarity signal",
            priority_score=0,
        )

    # ---- AI-only risk guard ---------------------------------------------------
    # Detects cues for the 4 sparse AI-only categories (Warranty/Service,
    # Contact Request, Price Complaint, Suggestion) BEFORE rule scoring,
    # so shared vocabulary (e.g. "price") doesn't leak into a rule category.
    ai_only_guard = detect_ai_only_risk(norm)
    if ai_only_guard is not None:
        return Classification(
            text=text,
            language=lang,
            primary_intent=None,
            secondary_intent=None,
            sentiment="Neutral",
            confidence="none",
            route="ai_only",
            ai_assisted=True,
            matched_keywords={},
            scores={},
            evidence_count=0,
            route_reason=ai_only_guard.reason,
            priority_score=0,
        )

    # ---- Keyword scoring ----------------------------------------------------
    scores, matches = _score_categories(norm)

    # ---- Order-confirmation context guard ------------------------------------
    # An order/receipt word ("gaththa", "ඕඩර් කරා") used inside a sentence
    # that also describes a problem should not be trusted as a rule-only
    # Order/Purchase Confirmation. Route to AI instead of forcing a category.
    confirmation_review = needs_confirmation_context_review(norm)

    if confirmation_review and scores:
        ranked_for_guard = sorted(
            scores.items(), key=lambda kv: kv[1], reverse=True
        )
        guarded_primary = ranked_for_guard[0][0]

        if (
            guarded_primary == "Order/Purchase Confirmation"
            or "Order/Purchase Confirmation" in scores
        ):
            return Classification(
                text=text,
                language=lang,
                primary_intent=guarded_primary,
                secondary_intent="Negative Feedback/Complaint",
                sentiment="Negative",
                confidence="medium",
                route="rules_ai_verify",
                ai_assisted=True,
                matched_keywords=matches,
                scores=scores,
                evidence_count=EVIDENCE.get((guarded_primary, lang), 0),
                route_reason=confirmation_review,
                priority_score=PRIORITY_WEIGHTS.get(guarded_primary, 0),
            )

    if not scores:
        return Classification(
            text=text, language=lang, primary_intent=None, secondary_intent=None,
            sentiment="Neutral", confidence="none", route="ai_only",
            ai_assisted=True, scores={},
            route_reason="No keyword rule matched — outside rule vocabulary coverage",
            priority_score=0,
        )

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    primary, primary_score = ranked[0]
    secondary = None
    if len(ranked) > 1 and ranked[1][1] >= SCORE_THRESHOLD:
        secondary = ranked[0 + 1][0]

    # ---- Below score threshold → not a confident rule match -----------------
    if primary_score < SCORE_THRESHOLD:
        return Classification(
            text=text, language=lang, primary_intent=primary, secondary_intent=None,
            sentiment=INTENT_DEFAULT_SENTIMENT.get(primary, "Neutral"),
            confidence="none", route="ai_only", ai_assisted=True,
            matched_keywords=matches, scores=scores,
            route_reason=f"Keyword score {primary_score} below threshold {SCORE_THRESHOLD}",
            priority_score=PRIORITY_WEIGHTS.get(primary, 0),
        )

    # ---- Ambiguous: two categories tied or nearly tied -----------------------
    if len(ranked) > 1 and (primary_score - ranked[1][1]) < CLEAR_WINNER_MARGIN \
            and ranked[1][1] >= SCORE_THRESHOLD:
        ev = EVIDENCE.get((primary, lang), 0)
        return Classification(
            text=text, language=lang, primary_intent=primary,
            secondary_intent=ranked[1][0],
            sentiment=INTENT_DEFAULT_SENTIMENT.get(primary, "Neutral"),
            confidence="medium", route="rules_ai_verify", ai_assisted=True,
            matched_keywords=matches, scores=scores, evidence_count=ev,
            route_reason=(f"Ambiguous: '{primary}' ({primary_score}) vs "
                          f"'{ranked[1][0]}' ({ranked[1][1]}) within margin — AI verifies"),
            priority_score=PRIORITY_WEIGHTS.get(primary, 0),
        )

    # ---- EVIDENCE-BASED CONFIDENCE (the core of the hybrid design) ----------
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

    # Sentiment: rule default, emoji as tiebreaker/override for feedback
    sentiment = INTENT_DEFAULT_SENTIMENT.get(primary, "Neutral")
    if primary in ("Positive Feedback", "Negative Feedback/Complaint"):
        if emoji_polarity != "Neutral":
            sentiment = emoji_polarity if primary != "Negative Feedback/Complaint" \
                        or emoji_polarity == "Negative" else sentiment

    return Classification(
        text=text, language=lang, primary_intent=primary,
        secondary_intent=secondary,
        sentiment=sentiment, confidence=conf, route=route, ai_assisted=ai,
        matched_keywords=matches, scores=scores, evidence_count=evidence,
        route_reason=reason,
        priority_score=PRIORITY_WEIGHTS.get(primary, 0),
    )