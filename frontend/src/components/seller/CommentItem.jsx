import { User, CheckCircle, SkipForward, RotateCcw } from "lucide-react";
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

const SENTIMENT_EMOJI = {
  positive: "😊",
  negative: "😞",
  neutral: "😐",
};

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

const CommentItem = ({ result, activeTab, onStatusChange }) => {
  const intent = INTENT_COLORS[result.intent] || INTENT_COLORS.general;
  const sentiment = SENTIMENT_EMOJI[result.sentiment] || "😐";

  return (
    <div className="comment-item">
      <div className="comment-avatar">
        <User size={16} />
      </div>
      <div className="comment-body">
        <div className="comment-top">
          <span className="comment-username">Customer {result.id}</span>
          <span className="comment-time">{timeAgo(result.created_at)}</span>
        </div>

        <p className="comment-text">{result.text}</p>

        <div className="comment-bottom">
          <div className="comment-labels">
            <span
              className="intent-label"
              style={{ background: intent.bg, color: intent.color }}
            >
              {intent.label}
            </span>
            <span className="sentiment-label">{sentiment}</span>
          </div>

          <div className="comment-actions">
            {activeTab === "new" && (
              <>
                <button
                  className="action-btn replied"
                  onClick={() => onStatusChange(result.id, "done")}
                >
                  <CheckCircle size={13} /> Replied
                </button>
                <button
                  className="action-btn skip"
                  onClick={() => onStatusChange(result.id, "pending")}
                >
                  <SkipForward size={13} /> Skip
                </button>
              </>
            )}
            {activeTab === "pending" && (
              <>
                <button
                  className="action-btn replied"
                  onClick={() => onStatusChange(result.id, "done")}
                >
                  <CheckCircle size={13} /> Replied
                </button>
                <button
                  className="action-btn reopen"
                  onClick={() => onStatusChange(result.id, "new")}
                >
                  <RotateCcw size={13} /> Move to New
                </button>
              </>
            )}
            {activeTab === "done" && (
              <button
                className="action-btn reopen"
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
