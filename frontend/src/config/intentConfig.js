export const INTENT_CONFIG = [
  {
    key: "purchase_intent",
    label: "Purchase Intent",
    emoji: "🛒",
    color: "#7c3aed",
  },
  {
    key: "product_inquiry",
    label: "Product Inquiry",
    emoji: "❓",
    color: "#0891b2",
  },
  {
    key: "price_inquiry",
    label: "Price Inquiry",
    emoji: "🏷️",
    color: "#d97706",
  },
  {
    key: "price_complaint",
    label: "Price Complaint",
    emoji: "😞",
    color: "#dc2626",
  },
  {
    key: "delivery_inquiry",
    label: "Delivery Inquiry",
    emoji: "🚚",
    color: "#2563eb",
  },
  {
    key: "location_availability",
    label: "Location/Availability",
    emoji: "📍",
    color: "#059669",
  },
  {
    key: "payment_method_inquiry",
    label: "Payment Method Inquiry",
    emoji: "💳",
    color: "#7c3aed",
  },
  {
    key: "warranty_service_inquiry",
    label: "Warranty/Service Inquiry",
    emoji: "🛡️",
    color: "#16a34a",
  },
  {
    key: "order_purchase_confirmation",
    label: "Order/Purchase Confirmation",
    emoji: "📋",
    color: "#0891b2",
  },
  {
    key: "positive_feedback",
    label: "Positive Feedback",
    emoji: "👍",
    color: "#16a34a",
  },
  {
    key: "negative_feedback_complaint",
    label: "Negative Feedback/Complaint",
    emoji: "😞",
    color: "#dc2626",
  },
  { key: "suggestion", label: "Suggestion", emoji: "💡", color: "#d97706" },
  {
    key: "contact_request",
    label: "Contact Request",
    emoji: "✉️",
    color: "#0891b2",
  },
  {
    key: "noise_off_topic",
    label: "Noise/Off-topic",
    emoji: "#️⃣",
    color: "#94a3b8",
  },
];

export const getIntentConfig = (key) =>
  INTENT_CONFIG.find((c) => c.key === key) || {
    key,
    label: key,
    emoji: "💬",
    color: "#94a3b8",
  };

export const LANGUAGE_LABELS = {
  english: "English",
  singlish: "Singlish",
  sinhala: "Sinhala",
  mixed: "Mixed",
  emoji: "Emoji",
};

export const LANGUAGE_COLORS = {
  english: "#2563eb",
  singlish: "#059669",
  sinhala: "#d97706",
  mixed: "#7c3aed",
  emoji: "#dc2626",
};
