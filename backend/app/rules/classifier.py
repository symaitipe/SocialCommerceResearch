"""
Hybrid Comment Classification Rule Engine
==========================================
Sri Lankan Facebook Social Commerce — English / Sinhala / Singlish / Mixed

Architecture:
  Layer 1 (this module): rule-based classification with evidence-based
           per-language confidence derived from the annotated corpus.
  Layer 2 (AI fallback): comments this engine cannot classify with
           sufficient evidence-backed confidence are routed to the LLM..
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional
from app.rules.routing_guards import (
    detect_ai_only_risk,
    contains_mobile_number,
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
    "Positive Feedback", "Negative Feedback/Complaint", "Noise/Off-topic",
]

# Order/Purchase Confirmation is not finalized by keyword rules. A detected
# mobile number routes the complete comment to Gemini, which checks whether a
# customer/recipient name + mobile number + delivery address are present
# together in an order-submission context.
CONTEXT_AI_CATEGORIES = frozenset({
    "Order/Purchase Confirmation",
})

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
#    Every keyword below was observed in the annotated corpus, UNLESS
#    explicitly marked source="synthetic" (see module docstring). Each
#    rule is (pattern, weight, is_regex, source). Weight reflects
#    specificity:
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
    source: str = "corpus"   # "corpus" = observed in annotated data
                              # "synthetic" = manually transliterated,
                              #   used only for unambiguous brand/service
                              #   names where phonetic variation is minimal

def R(p, w, rx=False, source="corpus"):
    return Rule(p, w, rx, source)

KEYWORD_RULES: dict[str, list[Rule]] = {

    # ── NEGATIVE FEEDBACK / COMPLAINT ─────────────────────────────────────
    "Negative Feedback/Complaint": [

        # ── Don't-buy warnings ─────────────────────────────────────────────
        R(r"\bganna? epa\b", 3, True),
        R("ගන්න එපා", 3),
        R("ගන්නෙපා", 3),
        R(r"\bgandepa\b", 3, True),
        R(r"\bdon'?t buy\b", 3, True),
        R(r"\bdonot buy\b", 3, True),
        R(r"\bdont take\b", 3, True),
        R("කවුරුවත් ගන්න", 3),
        R("කිසිම කෙනෙක් ගන්න", 3),

        # ── Not working / broken ────────────────────────────────────────────
        R(r"\bnot work", 3, True),
        R(r"\bwada n[aeh]", 3, True),
        R(r"\bvada n[aeh]", 3, True),
        R(r"\bwadak na", 3, True),
        R("වැඩ නෑ", 3),
        R("වැඩ කරන්නෙ නෑ", 3),
        R("වැඩ කරන්නේ නැ", 3),
        R(r"\bkaduna\b", 3, True),
        R(r"\bnot charging\b", 3, True),
        R(r"\bdoesn'?t work\b", 3, True),
        R(r"\bstopped working\b", 3, True),

        # ── Waste / worst / fake / cheating ─────────────────────────────────
        R(r"\bwaste\b", 3, True),
        R(r"\bworst\b", 3, True),
        R(r"\bfake\b", 3, True),
        R(r"\bcheat", 3, True),
        R(r"\bfraud", 3, True),
        R(r"\bscam", 3, True),
        R("සවුත්තු", 3),
        R(r"\bsavuth", 3, True),
        R(r"\bsawuth", 3, True),
        R("බොරු", 3),
        R("රවට්ට", 3),

        # ── Disappointment / quality complaints ─────────────────────────────
        R(r"\bdisappoint", 3, True),
        R(r"\bnot satisfied\b", 3, True),
        R(r"\bpoor quality\b", 3, True),
        R(r"\bnot good\b", 2, True),
        R(r"\bnot comfortable\b", 2, True),
        R(r"\bbad product\b", 3, True),
        R(r"\bnot quality\b", 2, True),
        R("පාඩුයි", 3),
        R("හිතුව තරම් කොලිටි නෑ", 3),
        R("කොලිටි නෑ", 3),

        # ── Wrong item / missing / damaged ──────────────────────────────────
        R(r"\bwrong (item|product|colou?r|size|model)\b", 3, True),
        R(r"\bmissing\b", 2, True),
        R(r"\bdamage", 2, True),
        R(r"\bbroken\b", 3, True),

        # "different item"
        R(r"\b(wena|vena) ekak\b", 3, True),
        R("වෙන එකක්", 3),

        # General Singlish:
        # "illapu ... nemei/neme"
        # Handles:
        # illapu eka nemei
        # illapu pata eka nemei
        # illapu size eka nemei
        # illapu model eka nemei
        R(
            r"\billapu\b.{0,30}\b(nemei|neme)\b",
            3,
            True
        ),

        # General Sinhala:
        # "ඉල්ලපු ... නෙමෙයි/නෙමේ"
        R(
            r"ඉල්ලපු.{0,30}(නෙමෙයි|නෙමේ)",
            3,
            True
        ),

        # Ordered/bought something, BUT a different/wrong item was involved.
        # Examples:
        # "order kra eth wena ekak awa"
        # "gaththa eth different item ekak"
        R(
            r"\b(order\s+(kara|kala|kra|kla)|gatta|gaththa)\b"
            r".{0,35}\b(eth|but)\b"
            r".{0,45}\b(wena|vena|different|wrong)\b",
            3,
            True
        ),

        # Ordered/bought something, BUT what arrived is not what was expected.
        #
        # Example:
        # "Ane mn order kra eth ewiyh tynne rosehip oil ek"
        #
        # Captures:
        # order kra + eth + ewiyh + tynne
        R(
            r"\b(order\s+(kara|kala|kra|kla)|gatta|gaththa)\b"
            r".{0,35}\b(eth|but)\b"
            r".{0,45}\b(awilla|avilla|ewila|ewilla|avila|awe|awa|ewiyh)\b"
            r".{0,25}\b(thiyenne|tiyenne|tyenne|tynne)\b",
            3,
            True
        ),

        # ── Order not arrived / seller not responding ───────────────────────
        R(r"\border? (eka )?thama n[ha]", 3, True),
        R(r"\banswer (karanne|krnne) na", 3, True),
        R(r"\bnot answering\b", 3, True),
        R(r"\breply karanne na", 3, True),
        R(r"\breact karanne n[ae]", 3, True),
        R("එකයි ඇවිත්", 2),
        R(r"\bstill waiting\b", 3, True),
        R(r"\bnever received\b", 3, True),

        # ── Other product problems ───────────────────────────────────────────
        R(r"\bahenne? na", 2, True),
        R("ඇහෙන්නෙ නෑ", 3),
        R("ඇහෙන්නේ", 1),
        R(r"\b(one|1) side not working\b", 3, True),
        R(r"\bahenawa adui\b", 3, True),
        R("බැලන්ස් නෑ", 3),

        # Supporting negative signals
        R(r"\bepa\b", 1, True),
        R("එපා", 1),
    ],

    # ── PAYMENT METHOD INQUIRY ────────────────────────────────────────────
    "Payment Method Inquiry": [
        R(r"\bkoko\b", 3, True), R(r"\binstallment", 3, True),
        R(r"\bcod\b", 3, True),
        R(r"\bcard payment", 3, True), R(r"\bcard eken\b", 3, True),
        R(r"\bpayment (method|plan|available|accept)", 3, True),
        R(r"\bbank transfer\b", 3, True),
        R(r"\bcash on delivery\b", 3, True),
        R(r"\bpay(ment)? .{0,12}(available|accept|puluwanda|thiyanawada)", 2, True),
        R("කොකො", 3, source="synthetic"),
        R(r"\bkokoo\b", 3, True, source="synthetic"),
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
        R(r"\bcourier\b", 3, True),
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

    # Order/Purchase Confirmation intentionally has no keyword rule block.
    # A mobile-number candidate is routed to Gemini for contextual verification.

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
        R("විතරද", 2), R(r"\bwitharada\b", 3, True),  R(r"\bavailable da\b", 3, True),
        # can-I-get questions
        R(r"\bganna puluwanda\b", 2, True), R(r"\bganna puluwnda\b", 2, True),
        R(r"\bganna barida\b", 2, True), R(r"\bganna berida\b", 2, True),
        R(r"\bcan (i|we) (get|purchase|buy)\b", 2, True),
        R("ගන්න පුළුවන්ද", 2), R("ගන්න බැරිද", 2),
        # genuine questions (interrogative structure present: "how to",
        # "kohomada"/how, "monawada"/what, "-da/ද" particle)
        R(r"\bmonawada\b", 2, True), R("මොනවද", 2), R("මොනවාද", 2),
        R(r"\bhow to use\b", 2, True),
        R(r"\bis it ok to use\b", 3, True), R(r"\bsafe (for|to)\b", 2, True),
        R(r"\bkohomada use\b", 2, True),
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
        R("හොදයි", 2), R("හොඳයි", 2), R("හොදම හොදයි", 3), R("හොදටම", 3),
        R(r"(^|\s)හොද(\s|$|,|\.|!|\?)", 2, True),
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
        R(r"^\s*$", 3, True),  # empty
        R(r"^nan$", 3, True),  # null artefacts
    ],
}

# ═══════════════════════════════════════════════════════════════════════════
# 5. EMOJI ANALYSER  (supplementary signal — Liu et al. 2021 support)
#    Still used to help decide INTENT for emoji-only comments; no longer
#    produces a separate sentiment output.
# ═══════════════════════════════════════════════════════════════════════════

POSITIVE_EMOJI = set("❤️🥰😍💪👍🔥💯♥️💗🤍💫😎🩵😊🙂👌✨🎉🥳😁💖")
NEGATIVE_EMOJI = set("😡🤮😭😒🚫💔😤😠🙄😞😢")

def analyze_emoji(text: str) -> tuple[str, int, int]:
    """Returns (polarity, positive_count, negative_count). Polarity here
    only decides which intent bucket an emoji-only comment falls into
    (Positive Feedback vs Negative Feedback/Complaint) — it is not
    exposed as a separate sentiment field."""
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
#    "quality ekak na", "hodai na". This decides INTENT (routes to
#    Negative Feedback/Complaint), not a sentiment label.
# ═══════════════════════════════════════════════════════════════════════════

# NEGATION_PATTERNS = [
#     re.compile(r"(hodai|hondai|hoda|good|quality|comfortable)\s+(na+|n[ae]h|නෑ|නැ)", re.I),
#     re.compile(r"(kisima|කිසිම)\s+(quality|hodak)?\s*(ekak)?\s*(na|නෑ)", re.I),
#     re.compile(r"quality\s+ekak\s+na", re.I),
#     re.compile(r"not\s+(good|great|nice|comfortable|working|worth|satisfied|recommended?)", re.I),
#     re.compile(r"(හොදයි|හොඳයි)\s*(නෑ|නැ)"),
#     re.compile(r"don'?t\s+recommend", re.I),
# ]

_NEGATION_FILLER = r"(?:the|a|an|that|so|really|very|quite|too)\s+"

NEGATION_PATTERNS = [
    re.compile(r"(hodai|hondai|hoda|good|quality|comfortable)\s+(na+|n[ae]h|නෑ|නැ)", re.I),
    re.compile(r"(kisima|කිසිම)\s+(quality|hodak)?\s*(ekak)?\s*(na|නෑ)", re.I),
    re.compile(r"quality\s+ekak\s+na", re.I),
    re.compile(
        rf"\bnot\s+(?:{_NEGATION_FILLER})?"
        r"(good|great|nice|comfortable|working|worth|satisfied|recommended?|"
        r"best|excellent|amazing|perfect|quality)\b",
        re.I
    ),
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
# 7. CLASSIFICATION RESULT
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Classification:
    text: str
    language: str
    primary_intent: Optional[str]
    secondary_intent: Optional[str]
    confidence: str                # "high" | "medium" | "none"
    route: str                     # "rules_only" | "rules_ai_verify" | "ai_only"
    ai_assisted: bool
    matched_keywords: dict = field(default_factory=dict)  # category -> [patterns]
    scores: dict = field(default_factory=dict)
    evidence_count: int = 0
    route_reason: str = ""

# ═══════════════════════════════════════════════════════════════════════════
# 8. THE CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════

# Minimum keyword score for a category to be considered "matched"
SCORE_THRESHOLD = 2
# Margin by which the winner must beat the runner-up to be unambiguous
CLEAR_WINNER_MARGIN = 2

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
                confidence="medium",
                route="rules_ai_verify", ai_assisted=True,
                matched_keywords={"Negative Feedback/Complaint": [f"emoji x{neg_e}"]},
                evidence_count=0,
                route_reason="Emoji-only negative — no corpus evidence for this cell; AI verifies",
            )
        return Classification(
            text=text, language=lang, primary_intent=None, secondary_intent=None,
            confidence="none", route="ai_only",
            ai_assisted=True, route_reason="Emoji/non-text with no polarity signal",
        )

    # ---- Order/Purchase Confirmation candidate guard -------------------------
    # A mobile number is only a routing signal. It is NOT enough by itself to
    # classify Order/Purchase Confirmation. Gemini must inspect the full comment
    # and verify that a customer/recipient name, mobile number, and delivery
    # address are provided together in an order-submission context.
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
            confidence="none",
            route="ai_only",
            ai_assisted=True,
            matched_keywords={},
            scores={},
            evidence_count=0,
            route_reason=ai_only_guard.reason,
        )

    # ---- Keyword scoring ----------------------------------------------------
    scores, matches = _score_categories(norm)

    if not scores:
        return Classification(
            text=text, language=lang, primary_intent=None, secondary_intent=None,
            confidence="none", route="ai_only",
            ai_assisted=True, scores={},
            route_reason="No keyword rule matched — outside rule vocabulary coverage",
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
            confidence="none", route="ai_only", ai_assisted=True,
            matched_keywords=matches, scores=scores,
            route_reason=f"Keyword score {primary_score} below threshold {SCORE_THRESHOLD}",
        )

    # ---- Ambiguous: two categories tied or nearly tied -----------------------
    if len(ranked) > 1 and (primary_score - ranked[1][1]) < CLEAR_WINNER_MARGIN \
            and ranked[1][1] >= SCORE_THRESHOLD:
        ev = EVIDENCE.get((primary, lang), 0)
        return Classification(
            text=text, language=lang, primary_intent=primary,
            secondary_intent=ranked[1][0],
            confidence="medium", route="rules_ai_verify", ai_assisted=True,
            matched_keywords=matches, scores=scores, evidence_count=ev,
            route_reason=(f"Ambiguous: '{primary}' ({primary_score}) vs "
                          f"'{ranked[1][0]}' ({ranked[1][1]}) within margin — AI verifies"),
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

    return Classification(
        text=text, language=lang, primary_intent=primary,
        secondary_intent=secondary,
        confidence=conf, route=route, ai_assisted=ai,
        matched_keywords=matches, scores=scores, evidence_count=evidence,
        route_reason=reason,
    )