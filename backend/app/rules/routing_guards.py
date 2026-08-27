"""
Routing guards for the SocialSell hybrid classifier.

Purpose
-------
These guards do not directly classify the four sparse AI-only categories.
They detect situations where a rule-only decision is unsafe and force the
comment to the AI layer.

Order/Purchase Confirmation is handled specially: the presence of a mobile
number is treated only as a routing signal. Gemini must inspect the complete
comment and decide whether it actually contains a customer/recipient name,
mobile number, and delivery address together as an order submission.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RoutingGuard:
    reason: str
    likely_group: str


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", str(text or "")).lower().strip()


def _has_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


# ---------------------------------------------------------------------------
# AI-ONLY RISK PATTERNS
# ---------------------------------------------------------------------------

PRICE_CONTEXT = (
    r"\bprice\b", r"\bprize\b", r"\bmila\b", r"\bgana\b", r"\bgaana\b",
    r"මිල", r"ගාන", r"ගණන්",
)

PRICE_COMPLAINT_CUES = (
    r"\btoo\s+(much|high|expensive)\b",
    r"\bvery\s+expensive\b",
    r"\boverpriced\b",
    r"\bexpensive\b",
    r"\bprice\s+(is\s+)?(high|increased|increase|up)\b",
    r"\b(wadi|wedi)\b",
    r"වැඩියි", r"වැඩි",
)

CONTACT_CHANNEL_CUES = (
    r"\bwhats?app\b", r"\bwebsite\b", r"\bweb\s*site\b",
    r"\bphone\b", r"\bcontact\b", r"\bhotline\b", r"\bnumber\b",
    r"\binbox\b", r"\bdm\b", r"\bmessage\b", r"\bcall\b",
    r"වට්ස්ඇප්", r"වට්සැප්", r"දුරකථන", r"නම්බර්",
)

WARRANTY_SERVICE_CUES = (
    r"\bwarrant(y|ies)\b", r"\bguarantee\b",
    r"\bservice\s*cent(er|re)\b",
    r"\brepair\b", r"\breplacement\b", r"\breplace\b",
    r"\breturn\b", r"\bexchange\b", r"\bclaim\b",
    r"\bafter[ -]?sales\b",
    r"වොරන්ටි", r"වගකීම", r"අලුත්වැඩියා",
)

SUGGESTION_CUES = (
    r"\bi\s+suggest\b", r"\bsuggestion\b", r"\bmy\s+suggestion\b",
    r"\byou\s+should\b", r"\bplease\s+(add|bring|include|make)\b",
    r"\bit\s+would\s+be\s+better\b", r"\bwould\s+be\s+better\b",
)


# ---------------------------------------------------------------------------
# ORDER/PURCHASE CONFIRMATION ROUTING SIGNAL
# ---------------------------------------------------------------------------

# Sri Lankan mobile formats such as:
#   0771234567
#   077 123 4567
#   077-123-4567
#   +94771234567
#   +94 77 123 4567
#   0094771234567
MOBILE_NUMBER_PATTERN = re.compile(
    r"(?<!\d)(?:\+94|0094|0)[\s-]*7\d(?:[\s-]*\d){7}(?!\d)"
)


def contains_mobile_number(text: str) -> bool:
    """
    Return True when the comment contains a Sri Lankan-style mobile number.

    The mobile number is NOT enough to classify the comment as
    Order/Purchase Confirmation. Its presence only forces AI review so Gemini
    can inspect whether name + mobile number + delivery address are present
    together in an order-submission context.
    """
    t = _norm(text)
    return bool(MOBILE_NUMBER_PATTERN.search(t))


def detect_ai_only_risk(text: str) -> Optional[RoutingGuard]:
    """
    Detect strong cues for one of the four sparse AI-only category groups.

    Important: this function does not assign the final intent. It only says
    that a rule-only decision is unsafe. The LLM must still classify using
    the complete 14-category taxonomy.
    """
    t = _norm(text)

    # Price Inquiry vs Price Complaint is a known collision.
    if _has_any(t, PRICE_CONTEXT) and _has_any(t, PRICE_COMPLAINT_CUES):
        return RoutingGuard(
            reason=(
                "Price wording appears together with dissatisfaction/high-price "
                "language; AI must distinguish Price Complaint from Price Inquiry"
            ),
            likely_group="price_complaint",
        )

    # Contact-channel failure can otherwise look like general negative feedback.
    if _has_any(t, CONTACT_CHANNEL_CUES):
        return RoutingGuard(
            reason=(
                "Comment refers to a contact channel or contact method; "
                "Contact Request is AI-only"
            ),
            likely_group="contact_request",
        )

    if _has_any(t, WARRANTY_SERVICE_CUES):
        return RoutingGuard(
            reason=(
                "Warranty/service/repair wording detected; "
                "Warranty/Service Inquiry is AI-only"
            ),
            likely_group="warranty_service",
        )

    if _has_any(t, SUGGESTION_CUES):
        return RoutingGuard(
            reason="Explicit suggestion wording detected; Suggestion is AI-only",
            likely_group="suggestion",
        )

    return None
