import { useNavigate } from "react-router-dom";
import "./FBRightPanel.css";

const INTENT_CONFIG = [
  { key: "purchase_intent", emoji: "🛒" },
  { key: "price_inquiry", emoji: "💰" },
  { key: "delivery_inquiry", emoji: "🚚" },
  { key: "product_inquiry", emoji: "📦" },
  { key: "feedback", emoji: "⭐" },
  { key: "general", emoji: "💬" },
];

const REGULAR_NOTIFS = [
  {
    avatar: "PS",
    text: "Philip Seneviratna reacted to your comment.",
    time: "19h",
  },
  {
    avatar: "RS",
    text: "Rasanga Sampath sent you a friend request.",
    time: "1w",
  },
  {
    avatar: "CD",
    text: "Charaka Dhananjaya invited you to join their group.",
    time: "2w",
  },
  {
    avatar: "DV",
    text: "Dilusha Vithanage accepted your friend request.",
    time: "2w",
  },
];

const POSTS = [
  { id: "chair", name: "Premium Quality Chair", emoji: "🪑" },
  { id: "tinea_herbal", name: "Tinea Herbal Product", emoji: "🌿" },
];

const FBRightPanel = ({ summaries }) => {
  const navigate = useNavigate();

  return (
    <div className="fb-right-panel">
      <h4 className="panel-title">Notifications</h4>

      <div className="notif-tabs">
        <span className="notif-tab active">All</span>
        <span className="notif-tab">Unread</span>
      </div>

      {/* Seller Alerts — at top of notifications */}
      {POSTS.map((post) => {
        const summary = summaries?.[post.id];
        const newCount = summary?.status_counts?.new || 0;
        const total = summary?.total || 0;
        if (total === 0) return null;

        return (
          <div
            key={post.id}
            className="seller-alert-card"
            onClick={() => navigate(`/post/${post.id}`)}
          >
            <div className="seller-alert-icon">🛍️</div>
            <div className="seller-alert-body">
              <div className="seller-alert-header">
                <span className="seller-alert-label">Seller Alert</span>
                {newCount > 0 && (
                  <span className="seller-new-badge">{newCount} new</span>
                )}
              </div>
              <div className="seller-alert-post">
                {post.emoji} {post.name}
              </div>
              <div className="seller-intent-chips">
                {INTENT_CONFIG.map((config) => {
                  const count = summary?.intent_counts?.[config.key];
                  if (!count) return null;
                  return (
                    <span key={config.key} className="seller-chip">
                      {config.emoji}
                      {count}
                    </span>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })}

      <div className="notif-divider">
        <span>Earlier</span>
      </div>

      {/* Regular Notifications */}
      {REGULAR_NOTIFS.map((notif, i) => (
        <div key={i} className="regular-notif">
          <div className="notif-avatar">{notif.avatar}</div>
          <div className="notif-body">
            <p className="notif-text">{notif.text}</p>
            <span className="notif-time">{notif.time}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default FBRightPanel;
