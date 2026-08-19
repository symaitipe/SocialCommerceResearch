import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getPostComments,
  getPost,
  getPostSummary,
  updateCommentStatus,
} from "../services/api";
import "./PostView.css";

const INTENT_CONFIG = [
  {
    key: "negative_feedback_complaint",
    label: "Negative Feedback",
    emoji: "🚨",
  },
  { key: "price_complaint", label: "Price Complaint", emoji: "💸" },
  { key: "purchase_intent", label: "Purchase Intent", emoji: "🛒" },
  { key: "order_details", label: "Order Details", emoji: "🔒" },
  { key: "contact_request", label: "Contact Request", emoji: "📞" },
  { key: "warranty_service_inquiry", label: "Warranty / Service", emoji: "🛠️" },
  { key: "payment_method_inquiry", label: "Payment Method", emoji: "💳" },
  { key: "price_inquiry", label: "Price Inquiry", emoji: "💰" },
  { key: "delivery_inquiry", label: "Delivery Inquiry", emoji: "🚚" },
  { key: "product_inquiry", label: "Product Inquiry", emoji: "📦" },
  { key: "location_availability", label: "Location", emoji: "📍" },
  {
    key: "order_purchase_confirmation",
    label: "Order Confirmation",
    emoji: "✅",
  },
  { key: "suggestion", label: "Suggestion", emoji: "💡" },
  { key: "positive_feedback", label: "Positive Feedback", emoji: "⭐" },
  { key: "noise_off_topic", label: "General", emoji: "💬" },
];

const URGENCY = {
  negative_feedback_complaint: "urgent",
  price_complaint: "urgent",
  contact_request: "urgent",
  purchase_intent: "money",
  order_details: "money",
  warranty_service_inquiry: "inquiry",
  payment_method_inquiry: "inquiry",
  price_inquiry: "inquiry",
  delivery_inquiry: "inquiry",
  product_inquiry: "inquiry",
  location_availability: "inquiry",
  order_purchase_confirmation: "inquiry",
  suggestion: "low",
  positive_feedback: "low",
  noise_off_topic: "low",
};

const TABS = [
  { key: "unread", label: "Unread", color: "#dc2626" },
  { key: "read_not_replied", label: "Not Replied", color: "#d97706" },
  { key: "replied", label: "Replied", color: "#16a34a" },
];

const AVATAR_COLORS = [
  "#1877f2",
  "#e11d48",
  "#7c3aed",
  "#059669",
  "#d97706",
  "#0891b2",
];

const avatarColor = (name = "") => {
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) % 997;
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
};

const timeAgo = (ts) => {
  if (!ts) return "";
  const diff = Date.now() - new Date(ts).getTime();
  const m = Math.floor(diff / 60000);
  const h = Math.floor(diff / 3600000);
  const d = Math.floor(diff / 86400000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  if (h < 24) return `${h}h ago`;
  return `${d}d ago`;
};

const DEFAULT_COLLAPSED = [
  "positive_feedback",
  "suggestion",
  "noise_off_topic",
];

const REPLY_TEMPLATES = {
  purchase_intent: {
    english: (date) =>
      `To confirm your order, please inbox us 📩\nYour details are safe with us 🔒`,
    sinhala: (date) =>
      `ඇණවුම සඳහා කරුණාකර inbox කරන්න 📩\nඔබේ විස්තර අපි රැකගන්නෙමු 🔒`,
    singlish: (date) =>
      `Order confirm karanna inbox karanna 📩\nPrivate ah details denna 🔒`,
    mixed: (date) => `Order confirm කරන්න inbox කරන්න 📩🔒`,
  },
  order_purchase_confirmation: {
    english: (date) => `Order confirmed on ${date} ✅`,
    sinhala: (date) => `ඇණවුම තහවුරු කරන ලදී - ${date} ✅`,
    singlish: (date) => `Order eka confirm - ${date} ✅`,
    mixed: (date) => `Order confirmed - ${date} ✅`,
  },
  price_inquiry: {
    english: () => `Please inbox us for pricing details 📩`,
    sinhala: () => `මිල විස්තර සඳහා inbox කරන්න 📩`,
    singlish: () => `Price details inbox karanna 📩`,
    mixed: () => `Price details inbox කරන්න 📩`,
  },
  price_complaint: {
    english: () =>
      `We understand your concern about pricing. Please inbox us so we can explain and help 🙏`,
    sinhala: () =>
      `මිල සම්බන්ධව ඔබේ අදහස තේරෙනවා. කරුණාකර inbox කරන්න, අපි උදව් කරන්නම් 🙏`,
    singlish: () => `Price eka gana yanna inbox karanna, api discuss karamu 🙏`,
    mixed: () => `Price gana inbox කරන්න, discuss කරමු 🙏`,
  },
  delivery_inquiry: {
    english: () => `We deliver island-wide! Inbox us for details 🚚`,
    sinhala: () => `දිවයිනේ ඕනෑම තැනකට delivery කරනවා! Inbox කරන්න 🚚`,
    singlish: () => `Island wide deliver karanawa! Inbox karanna 🚚`,
    mixed: () => `Island wide delivery! Inbox කරන්න 🚚`,
  },
  location_availability: {
    english: () =>
      `Please inbox us for our location and availability details 📍`,
    sinhala: () => `ස්ථානය/තිබෙන ස්ථාන ගැන inbox කරන්න 📍`,
    singlish: () => `Location eka gana inbox karanna 📍`,
    mixed: () => `Location eka gana inbox කරන්න 📍`,
  },
  payment_method_inquiry: {
    english: () =>
      `We accept cash on delivery, bank transfer and Koko! Inbox for more 💳`,
    sinhala: () =>
      `Cash on delivery, bank transfer, Koko ලබාගත හැක! Inbox කරන්න 💳`,
    singlish: () =>
      `Cash on delivery, bank transfer, koko thiyenawa! Inbox karanna 💳`,
    mixed: () => `Payment options ගැන inbox කරන්න 💳`,
  },
  warranty_service_inquiry: {
    english: () =>
      `Please inbox us with your order details for warranty/service support 🛠️`,
    sinhala: () => `Warranty/service සඳහා ඔබේ ඇණවුම් විස්තර සමඟ inbox කරන්න 🛠️`,
    singlish: () => `Warranty eka gana order details ekka inbox karanna 🛠️`,
    mixed: () => `Warranty ගැන order details ekka inbox කරන්න 🛠️`,
  },
  contact_request: {
    english: () =>
      `You can reach us right here on inbox — we're happy to help 📞`,
    sinhala: () => `මෙතනින්ම inbox කරන්න, අපි උදව් කරන්නම් 📞`,
    singlish: () => `Meken inbox karanna, api help karannam 📞`,
    mixed: () => `Inbox කරන්න, api help කරන්නම් 📞`,
  },
  negative_feedback_complaint: {
    english: () =>
      `We're sorry to hear this. Please inbox us so we can resolve this 🙏`,
    sinhala: () => `කණගාටුයි. කරුණාකර inbox කරන්න, අපි විසඳුමක් ගනිමු 🙏`,
    singlish: () => `Sorry machan. Inbox karanna, api resolve karannam 🙏`,
    mixed: () => `Sorry. Inbox කරන්න, අපි help කරන්නම් 🙏`,
  },
  suggestion: {
    english: () => `Thank you for the suggestion, we really appreciate it! 🙏`,
    sinhala: () => `ඔබේ යෝජනාවට ස්තූතියි! අගය කරනවා 🙏`,
    singlish: () => `Suggestion eka gana thanks machan! 🙏`,
    mixed: () => `Suggestion එකට ස්තූතියි! 🙏`,
  },
  positive_feedback: {
    english: () => `Thank you so much! ❤️`,
    sinhala: () => `ස්තූතියි! ❤️`,
    singlish: () => `Thanks machan! ❤️`,
    mixed: () => `ස්තූතියි! Thank you ❤️`,
  },
};

const ReplyBox = ({ comment, onClose, onReplied }) => {
  const today = new Date().toISOString().split("T")[0];
  const lang = comment.language || "english";
  const intent = comment.intent || "general";
  const templates = REPLY_TEMPLATES[intent]?.[lang]
    ? [REPLY_TEMPLATES[intent][lang](today)]
    : [];

  const [replyText, setReplyText] = useState(templates[0] || "");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  const handleSend = async () => {
    if (!replyText.trim()) return;
    setSending(true);
    setError(null);
    try {
      const res = await fetch(
        `http://localhost:8000/posts/comments/${comment.id}/reply`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: replyText }),
        },
      );
      const data = await res.json();
      if (data.success) {
        onReplied();
      } else {
        setError(data.error || "Failed to send reply");
      }
    } catch (e) {
      setError("Network error — check backend");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="reply-box">
      {templates.length > 0 && (
        <div className="reply-templates">
          <span className="reply-template-label">💡 Suggested reply:</span>
          {templates.map((t, i) => (
            <button
              key={i}
              className="reply-template-btn"
              onClick={() => setReplyText(t)}
            >
              {t}
            </button>
          ))}
        </div>
      )}
      <textarea
        value={replyText}
        onChange={(e) => setReplyText(e.target.value)}
        placeholder="Type your reply..."
        rows={3}
      />
      {error && <div className="reply-error">{error}</div>}
      <div className="reply-actions">
        <button className="reply-cancel" onClick={onClose}>
          Cancel
        </button>
        <button
          className="reply-send"
          onClick={handleSend}
          disabled={sending || !replyText.trim()}
        >
          {sending ? "Sending..." : "Send Reply →"}
        </button>
      </div>
    </div>
  );
};

const CommentRow = ({ comment, activeTab, onStatusChange, showToast }) => {
  const [showReply, setShowReply] = useState(false);

  const handleMarkRead = async () => {
    await onStatusChange(comment.id, "read_not_replied");
    showToast("✓ Marked as read");
  };

  const handleMarkReplied = async () => {
    await onStatusChange(comment.id, "replied");
    showToast("✓ Marked as replied");
  };

  return (
    <div className={`pv-comment ${comment.status}`}>
      <div className="pv-comment-top">
        <div className="pv-commenter">
          <div
            className="pv-avatar"
            style={{ background: avatarColor(comment.commenter_name) }}
          >
            {(comment.commenter_name || "C").charAt(0).toUpperCase()}
          </div>
          <div>
            <span className="pv-commenter-name">
              {comment.commenter_name || "Customer"}
            </span>
            <span className="pv-comment-time">
              {timeAgo(comment.created_at)}
            </span>
          </div>
        </div>
      </div>

      <p className="pv-comment-text">{comment.text}</p>

      <div className="pv-comment-actions">
        {activeTab !== "replied" && (
          <button
            className="pv-btn primary"
            onClick={() => {
              if (activeTab === "unread") {
                onStatusChange(comment.id, "read_not_replied");
              }
              setShowReply(!showReply);
            }}
          >
            💬 Reply
          </button>
        )}
        {activeTab === "unread" && (
          <button className="pv-btn subtle" onClick={handleMarkRead}>
            Mark read
          </button>
        )}
        {activeTab === "read_not_replied" && (
          <button className="pv-btn subtle" onClick={handleMarkReplied}>
            Mark replied
          </button>
        )}
        {activeTab === "replied" && (
          <button
            className="pv-btn subtle"
            onClick={() => onStatusChange(comment.id, "read_not_replied")}
          >
            ↩ Reopen
          </button>
        )}
        {comment.facebook_comment_url && (
          <a
            href={comment.facebook_comment_url}
            target="_blank"
            rel="noreferrer"
            className="pv-btn subtle"
          >
            View on FB ↗
          </a>
        )}
      </div>

      {showReply && (
        <ReplyBox
          comment={comment}
          onClose={() => setShowReply(false)}
          onReplied={() => {
            onStatusChange(comment.id, "replied");
            setShowReply(false);
            showToast("✅ Reply sent to Facebook");
          }}
        />
      )}
    </div>
  );
};

const PostView = () => {
  const { postId } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [activeTab, setActiveTab] = useState("unread");
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [collapsed, setCollapsed] = useState(
    Object.fromEntries(DEFAULT_COLLAPSED.map((k) => [k, true])),
  );
  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const toggleGroup = (key) =>
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));

  const load = async () => {
    setLoading(true);
    try {
      const [p, c, s] = await Promise.all([
        getPost(postId),
        getPostComments(postId),
        getPostSummary(postId),
      ]);
      setPost(p);
      setComments(c);
      setSummary(s);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [postId]);

  const handleStatusChange = async (commentId, status) => {
    await updateCommentStatus(commentId, status);
    setComments((prev) =>
      prev.map((c) => (c.id === commentId ? { ...c, status } : c)),
    );
  };

  const handleMarkAllRead = async () => {
    const unread = comments.filter((c) => c.status === "unread");
    await Promise.all(
      unread.map((c) => updateCommentStatus(c.id, "read_not_replied")),
    );
    setComments((prev) =>
      prev.map((c) =>
        c.status === "unread" ? { ...c, status: "read_not_replied" } : c,
      ),
    );
    showToast(`✓ ${unread.length} comments marked as read`);
  };

  const tabComments = comments.filter((c) => c.status === activeTab);
  const getCount = (tab) => comments.filter((c) => c.status === tab).length;

  const groupedByIntent = INTENT_CONFIG.map((config) => ({
    ...config,
    items: tabComments
      .filter((c) => c.intent === config.key)
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)),
  })).filter((g) => g.items.length > 0);

  if (loading) return <div className="pv-loading">Loading...</div>;
  if (!post) return <div className="pv-loading">Post not found.</div>;

  return (
    <div className="pv-page">
      {/* Header */}
      <div className="pv-header">
        <button className="pv-back" onClick={() => navigate("/")}>
          ← Back
        </button>
        <div className="pv-header-info">
          <span className="pv-title">{post.title || post.facebook_url}</span>
          <span className="pv-meta">
            {post.total_comments} comments · synced{" "}
            {timeAgo(post.last_fetched_at)}
            {post.last_sync_new_count > 0 && (
              <span className="pv-new-badge">
                +{post.last_sync_new_count} new
              </span>
            )}
          </span>
        </div>
        <a
          href={post.facebook_url}
          target="_blank"
          rel="noreferrer"
          className="pv-fb-link"
        >
          View on Facebook ↗
        </a>
      </div>

      {/* Summary Pills */}
      {summary && (
        <div className="pv-summary">
          {INTENT_CONFIG.filter(
            (c, i, arr) =>
              summary.intent_counts?.[c.key] > 0 &&
              arr.findIndex((x) => x.key === c.key) === i,
          ).map((c) => (
            <span key={c.key} className="pv-summary-pill">
              {c.emoji} {c.label}{" "}
              <strong>{summary.intent_counts[c.key]}</strong>
            </span>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="pv-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`pv-tab ${activeTab === tab.key ? "active" : ""}`}
            style={
              activeTab === tab.key
                ? { borderBottomColor: tab.color, color: tab.color }
                : {}
            }
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
            <span className="pv-tab-count">{getCount(tab.key)}</span>
          </button>
        ))}

        {activeTab === "unread" && getCount("unread") > 0 && (
          <button className="pv-mark-all" onClick={handleMarkAllRead}>
            ✓ Mark all as read
          </button>
        )}
      </div>

      {/* Comment Groups */}
      <div className="pv-feed">
        {groupedByIntent.length === 0 && (
          <div className="pv-empty">
            {activeTab === "unread" && "🎉 All caught up! No unread comments."}
            {activeTab === "read_not_replied" &&
              "📭 No comments waiting for reply."}
            {activeTab === "replied" && "📋 No replied comments yet."}
          </div>
        )}

        {groupedByIntent.map((group) => (
          <div
            key={group.key}
            className={`pv-group urgency-${URGENCY[group.key] || "low"}`}
          >
            <div
              className="pv-group-header"
              onClick={() => toggleGroup(group.key)}
            >
              <span>
                {group.emoji} {group.label}
              </span>
              <span className="pv-group-right">
                <span className="pv-group-count">{group.items.length}</span>
                <span className="pv-collapse-icon">
                  {collapsed[group.key] ? "▸" : "▾"}
                </span>
              </span>
            </div>

            {!collapsed[group.key] &&
              group.items.map((comment) => (
                <CommentRow
                  key={comment.id}
                  comment={comment}
                  activeTab={activeTab}
                  onStatusChange={handleStatusChange}
                  showToast={showToast}
                />
              ))}
          </div>
        ))}
      </div>

      {/* Toast */}
      {toast && <div className="pv-toast">{toast}</div>}
    </div>
  );
};

export default PostView;
