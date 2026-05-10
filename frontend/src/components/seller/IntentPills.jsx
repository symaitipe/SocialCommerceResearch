import "./IntentPills.css";

const INTENT_CONFIG = [
  { key: "all", emoji: "💬", label: "All" },
  { key: "purchase_intent", emoji: "🛒", label: "Buy" },
  { key: "price_inquiry", emoji: "💰", label: "Price" },
  { key: "delivery_inquiry", emoji: "🚚", label: "Delivery" },
  { key: "product_inquiry", emoji: "📦", label: "Product" },
  { key: "feedback", emoji: "⭐", label: "Feedback" },
  { key: "general", emoji: "🗣️", label: "General" },
];

const IntentPills = ({ activeIntent, onSelect, intentCounts }) => {
  return (
    <div className="intent-pills">
      {INTENT_CONFIG.map((config) => {
        const count =
          config.key === "all"
            ? Object.values(intentCounts || {}).reduce((a, b) => a + b, 0)
            : intentCounts?.[config.key] || 0;

        if (config.key !== "all" && count === 0) return null;

        return (
          <button
            key={config.key}
            className={`intent-pill ${activeIntent === config.key ? "active" : ""}`}
            onClick={() => onSelect(config.key)}
          >
            {config.emoji} {config.label}
            {count > 0 && <span className="pill-count">{count}</span>}
          </button>
        );
      })}
    </div>
  );
};

export default IntentPills;
