import { ChevronRight, MessageCircle } from "lucide-react";
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

const PostCard = ({ post, onClick }) => {
  const newCount = post.new_count || 0;
  const total = post.total_comments || 0;

  return (
    <div className="post-card" onClick={onClick}>
      <div className="post-card-info">
        <div className="post-card-title-row">
          <span className="post-card-title">
            {post.title || post.facebook_url}
          </span>
          {newCount > 0 && <span className="new-badge">{newCount} new</span>}
        </div>
        <span className="post-card-url">{post.facebook_url}</span>
        <div className="post-card-footer">
          <MessageCircle size={13} />
          <span>{total} comments</span>
          <span className="dot">·</span>
          <span>synced {timeAgo(post.last_fetched_at)}</span>
        </div>
      </div>
      <ChevronRight size={18} className="post-card-arrow" />
    </div>
  );
};

export default PostCard;
