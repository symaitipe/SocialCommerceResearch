import { Bot, User, CheckCircle, Clock, RotateCcw } from "lucide-react";
import "./CommentItem.css";

const INTENT_COLORS = {
  price_inquiry: { bg: "#dbeafe", color: "#1d4ed8", label: "Price Inquiry" },
  delivery_inquiry: { bg: "#fef9c3", color: "#92400e", label: "Delivery" },
  purchase_intent: {
    bg: "#dcfce7",
    color: "#15803d",
    label: "Purchase Intent",
  },
  product_inquiry: {
    bg: "#ede9fe",
    color: "#7c3aed",
    label: "Product Inquiry",
  },
  feedback: { bg: "#fce7f3", color: "#be185d", label: "Feedback" },
  general: { bg: "#f1f5f9", color: "#64748b", label: "General" },
};

const SENTIMENT_COLORS = {
  positive: { bg: "#dcfce7", color: "#15803d", emoji: "😊" },
  negative: { bg: "#fee2e2", color: "#dc2626", emoji: "😞" },
  neutral: { bg: "#f1f5f9", color: "#64748b", emoji: "😐" },
};

const LANGUAGE_LABELS = {
  english: "EN",
  sinhala: "SI",
  singlish: "SG",
  mixed: "MX",
};

const CommentItem = ({ result, index, activeTab, onStatusChange }) => {
  const intent = INTENT_COLORS[result.intent] || INTENT_COLORS.general;
  const sentiment =
    SENTIMENT_COLORS[result.sentiment] || SENTIMENT_COLORS.neutral;
  const language = LANGUAGE_LABELS[result.language] || "EN";

  const timeAgo = (timestamp) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    const hrs = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    if (hrs < 24) return `${hrs}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="comment-item">
      <div className="comment-avatar">
        <User size={18} />
      </div>
      <div className="comment-body">
        <div className="comment-header">
          <span className="comment-username">Customer {result.id}</span>
          <span className="language-badge">{language}</span>
          {result.ai_assisted === 1 && (
            <span className="ai-badge">
              <Bot size={11} /> AI
            </span>
          )}
          <span className="comment-time">{timeAgo(result.created_at)}</span>
        </div>

        <p className="comment-text">{result.text}</p>

        <div className="comment-footer">
          <div className="comment-tags">
            <span
              className="tag"
              style={{ background: intent.bg, color: intent.color }}
            >
              {intent.label}
            </span>
            <span
              className="tag"
              style={{ background: sentiment.bg, color: sentiment.color }}
            >
              {sentiment.emoji} {result.sentiment}
            </span>
          </div>

          {/* Status Action Buttons */}
          <div className="comment-actions">
            {activeTab === "new" && (
              <>
                <button
                  className="action-btn pending"
                  onClick={() => onStatusChange(result.id, "pending")}
                >
                  <Clock size={13} /> Mark Pending
                </button>
                <button
                  className="action-btn done"
                  onClick={() => onStatusChange(result.id, "done")}
                >
                  <CheckCircle size={13} /> Done
                </button>
              </>
            )}
            {activeTab === "pending" && (
              <>
                <button
                  className="action-btn done"
                  onClick={() => onStatusChange(result.id, "done")}
                >
                  <CheckCircle size={13} /> Mark Done
                </button>
                <button
                  className="action-btn reset"
                  onClick={() => onStatusChange(result.id, "new")}
                >
                  <RotateCcw size={13} /> Move to New
                </button>
              </>
            )}
            {activeTab === "done" && (
              <button
                className="action-btn reset"
                onClick={() => onStatusChange(result.id, "pending")}
              >
                <RotateCcw size={13} /> Reopen
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommentItem;
