"""
Routing guards for the SocialSell hybrid classifier.

Purpose
-------
These guards DO NOT classify the four AI-only categories themselves.
They only detect situations where a rule-only decision is unsafe and
force the comment to the AI layer.

This preserves the research design:
- 10 categories can be handled by rules when evidence/confidence is enough.
- 4 sparse categories remain AI-only.
- Shared vocabulary should not let AI-only comments leak into rule categories.
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
# ORDER-CONFIRMATION CONTEXT GUARD
# ---------------------------------------------------------------------------

CONFIRMATION_CUES = (
    r"\bgatta\b", r"\bgaththa\b", r"\bhambuna\b", r"\bhambune\b",
    r"\breceived\b", r"\bgot\s+(mine|my|it|the)\b", r"\bordered\b",
    r"ඕඩර්\s*(කරා|කලා)", r"ඔඩර්\s*(කරා|කලා)",
    r"ලැබුණ", r"හම්බුන",
)

NEGATIVE_CONTEXT_CUES = (
    r"\bnot\s+(work|working|good|quality|satisfied)\b",
    r"\bdoesn'?t\s+work\b", r"\bstopped\s+working\b",
    r"\b(wada|vada)\s+n[aeh]+\b",
    r"\bkaduna\b", r"\bbroken\b",
    r"\bpoor\b", r"\bbad\b", r"\bworst\b", r"\bwaste\b",
    r"වැඩ\s*(නෑ|නැ)", r"නරක", r"කැඩුන", r"කැඩුණ",
    r"හොඳ\s*(නෑ|නැ)", r"හොද\s*(නෑ|නැ)",
)


def detect_ai_only_risk(text: str) -> Optional[RoutingGuard]:
    """
    Detect strong cues for one of the four AI-only category groups.

    Important: this function does NOT assign the final intent.  It only says
    that a rule-only decision is unsafe.  The LLM must still classify using
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


def needs_confirmation_context_review(text: str) -> Optional[str]:
    """
    Detect an order/receipt word used inside a negative sentence.

    Example:
        "gaththa eka wada na"

    A token such as "gaththa" should not make Order/Purchase Confirmation the
    final rule result when the surrounding sentence clearly describes a problem.
    """
    t = _norm(text)

    if _has_any(t, CONFIRMATION_CUES) and _has_any(t, NEGATIVE_CONTEXT_CUES):
        return (
            "Order/receipt wording appears together with negative context; "
            "require AI verification"
        )

    return None
