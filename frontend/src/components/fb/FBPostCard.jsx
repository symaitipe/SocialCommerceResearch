import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ThumbsUp, MessageCircle, Share2, MoreHorizontal } from "lucide-react";
import FBComment from "./FBComment";
import "./FBPostCard.css";

const FBPostCard = ({ post, comments = [], isSeller = false }) => {
  const navigate = useNavigate();
  const [showComments, setShowComments] = useState(false);
  const [liked, setLiked] = useState(false);

  const previewComments = comments.slice(0, 3);

  return (
    <div className="fb-post-card">
      {/* Post Header */}
      <div className="fb-post-header">
        <div className="fb-post-avatar">🛍️</div>
        <div className="fb-post-meta">
          <span className="fb-post-author">Sri Lanka Seller</span>
          <span className="fb-post-time">9h · 🌐</span>
        </div>
        <button className="fb-post-more">
          <MoreHorizontal size={20} />
        </button>
      </div>

      {/* Post Content */}
      <div className="fb-post-content">
        <p className="fb-post-text">{post.description}</p>
      </div>

      {/* Product Image Area */}
      <div className="fb-post-image">
        <div className="fb-product-display">
          <span className="fb-product-emoji">{post.emoji}</span>
          <div className="fb-product-info">
            <span className="fb-product-name">{post.name}</span>
            <span className="fb-product-price">{post.price}</span>
            <span className="fb-product-cta">Comment to order ✉️</span>
          </div>
        </div>
      </div>

      {/* Reactions Row */}
      <div className="fb-post-stats">
        <span>👍❤️😍 {liked ? 538 : 537}</span>
        <div className="fb-post-stats-right">
          <span
            className="fb-comments-count"
            onClick={() => setShowComments(!showComments)}
          >
            {comments.length} comments
          </span>
          {isSeller && (
            <span
              className="fb-seller-view-btn"
              onClick={() => navigate(`/post/${post.id}`)}
            >
              📊 Seller View
            </span>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="fb-post-divider" />
      <div className="fb-post-actions">
        <button
          className={`fb-action-btn ${liked ? "liked" : ""}`}
          onClick={() => setLiked(!liked)}
        >
          <ThumbsUp size={18} /> Like
        </button>
        <button
          className="fb-action-btn"
          onClick={() => setShowComments(!showComments)}
        >
          <MessageCircle size={18} /> Comment
        </button>
        <button className="fb-action-btn">
          <Share2 size={18} /> Share
        </button>
      </div>

      {/* Comments Preview */}
      {showComments && (
        <div className="fb-comments-section">
          <div className="fb-comment-input">
            <div className="fb-comment-avatar">SY</div>
            <input placeholder="Write a comment..." />
          </div>
          {previewComments.map((comment, i) => (
            <FBComment key={i} comment={comment} />
          ))}
          {comments.length > 3 && (
            <button
              className="fb-view-all-btn"
              onClick={() => navigate(`/post/${post.id}`)}
            >
              View all {comments.length} comments
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default FBPostCard;
