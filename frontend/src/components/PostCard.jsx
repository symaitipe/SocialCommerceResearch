import { MessageCircle, RefreshCw, ArrowRight, Package } from "lucide-react";
import "./PostCard.css";

const timeAgo = (timestamp) => {
  if (!timestamp) return "never";
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  const hrs = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (hrs < 24) return `${hrs}h ago`;
  return `${days}d ago`;
};

// No real product image is fetched from Facebook yet (would need the
// Graph API attachments{media} field on the post). This is a deliberate
// placeholder block, not a fake photo.
const PostThumbnail = () => (
  <div className="post-thumb-placeholder">
    <Package size={22} />
  </div>
);

const PostCard = ({ post, progress, onOpen, onSync }) => {
  const newCount = post.last_sync_new_count || 0;
  const total = post.total_comments || 0;
  const isSyncing = !!progress && !progress.done;

  return (
    <div className="post-card">
      <div className="post-card-main" onClick={onOpen}>
        <PostThumbnail />
        <div className="post-card-info">
          <div className="post-card-title-row">
            <span className="post-card-title">
              {post.title || post.facebook_url}
            </span>
            <span className="tracking-badge">Tracking</span>
          </div>
          <div className="post-card-meta">
            <span className="post-card-meta-item">
              <MessageCircle size={13} />
              {total} comments
            </span>
            <span className="post-card-meta-dot">·</span>
            <span>Last synced {timeAgo(post.last_fetched_at)}</span>
          </div>
        </div>
      </div>

      <div className="post-card-actions">
        <button
          className="sync-btn"
          onClick={(e) => {
            e.stopPropagation();
            onSync();
          }}
          disabled={isSyncing}
        >
          <RefreshCw size={14} className={isSyncing ? "spin" : ""} />
          {isSyncing ? "Syncing..." : "Sync now"}
        </button>
        {newCount > 0 && !isSyncing && (
          <span className="new-badge">{newCount} new</span>
        )}
        <button className="post-card-arrow" onClick={onOpen} title="Open post">
          <ArrowRight size={16} />
        </button>
      </div>

      {isSyncing && (
        <div className="post-card-progress">
          <div className="post-card-progress-track">
            <div className="post-card-progress-fill" />
          </div>
          <span className="post-card-progress-text">
            {progress.total > 0
              ? `${progress.total} fetched...`
              : "Starting..."}
          </span>
        </div>
      )}
    </div>
  );
};

export default PostCard;
