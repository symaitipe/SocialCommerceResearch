import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ChevronLeft } from "lucide-react";
import FBLayout from "../components/fb/FBLayout";
import FBComment from "../components/fb/FBComment";
import IntentPills from "../components/seller/IntentPills";
import CommentFeed from "../components/seller/CommentFeed";
import {
  getCommentsByCategory,
  getSummaryByCategory,
  analyzeSingle,
  updateCommentStatus,
} from "../services/api";
import "./PostDetail.css";

const PRODUCT_INFO = {
  chair: {
    name: "Premium Quality Chair",
    emoji: "🪑",
    price: "Rs. 15,000",
    description: "Premium Quality Office & Home Chair — Now Available!",
  },
  tinea_herbal: {
    name: "Tinea Herbal Product",
    emoji: "🌿",
    price: "Rs. 1,200",
    description: "Natural Herbal Treatment — Tinea Herbal Product",
  },
  general: {
    name: "General Product Post",
    emoji: "📦",
    price: "Contact for price",
    description: "General product post.",
  },
};

const PostDetail = () => {
  const { category } = useParams();
  const navigate = useNavigate();
  const product = PRODUCT_INFO[category] || PRODUCT_INFO.general;

  const [comments, setComments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [activeIntent, setActiveIntent] = useState("all");
  const [activeTab, setActiveTab] = useState("new");
  const [newComment, setNewComment] = useState("");
  const [adding, setAdding] = useState(false);

  const fetchData = async () => {
    const [cmts, smry] = await Promise.all([
      getCommentsByCategory(category),
      getSummaryByCategory(category),
    ]);
    setComments(cmts);
    setSummary(smry);
  };

  useEffect(() => {
    fetchData();
  }, [category]);

  const handleAdd = async () => {
    if (!newComment.trim()) return;
    setAdding(true);
    await analyzeSingle(newComment.trim(), category);
    setNewComment("");
    await fetchData();
    setAdding(false);
  };

  const handleStatusChange = async (id, status) => {
    await updateCommentStatus(id, status);
    setComments((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status } : c)),
    );
  };

  const filteredComments =
    activeIntent === "all"
      ? comments
      : comments.filter((c) => c.intent === activeIntent);

  return (
    <FBLayout showRight={false}>
      <div className="post-detail">
        {/* Back */}
        <button className="pd-back-btn" onClick={() => navigate("/")}>
          <ChevronLeft size={20} /> Back to Feed
        </button>

        <div className="pd-layout">
          {/* Left — FB style post + comments */}
          <div className="pd-left">
            <div className="pd-post-card">
              <div className="pd-post-header">
                <div className="pd-avatar">🛍️</div>
                <div>
                  <div className="pd-author">Sri Lanka Seller</div>
                  <div className="pd-time">9h · 🌐</div>
                </div>
              </div>
              <p className="pd-post-text">{product.description}</p>
              <div className="pd-product-banner">
                <span className="pd-product-emoji">{product.emoji}</span>
                <div>
                  <div className="pd-product-name">{product.name}</div>
                  <div className="pd-product-price">{product.price}</div>
                </div>
              </div>

              {/* Raw comments in FB style */}
              <div className="pd-fb-comments">
                <div className="pd-comments-title">
                  💬 {comments.length} comments
                </div>
                {comments.slice(0, 5).map((c, i) => (
                  <FBComment key={i} comment={c} />
                ))}
                {comments.length > 5 && (
                  <span className="pd-more-comments">
                    + {comments.length - 5} more comments below ↓
                  </span>
                )}
              </div>

              {/* Add comment */}
              <div className="pd-add-comment">
                <div className="pd-add-avatar">SY</div>
                <input
                  placeholder="Add a comment as a customer..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                />
                <button
                  className="pd-add-btn"
                  onClick={handleAdd}
                  disabled={adding}
                >
                  {adding ? "..." : "➤"}
                </button>
              </div>
            </div>
          </div>

          {/* Right — Seller Intelligence Panel */}
          <div className="pd-right">
            <div className="pd-seller-panel">
              <div className="pd-seller-header">
                <span className="pd-seller-title">📊 Seller Intelligence</span>
                <span className="pd-seller-sub">CommentIQ Analysis</span>
              </div>

              {/* Status counts */}
              <div className="pd-status-row">
                <div className="pd-stat new">
                  <span>{summary?.status_counts?.new || 0}</span>
                  <label>🔴 New</label>
                </div>
                <div className="pd-stat pending">
                  <span>{summary?.status_counts?.pending || 0}</span>
                  <label>🟡 Pending</label>
                </div>
                <div className="pd-stat done">
                  <span>{summary?.status_counts?.done || 0}</span>
                  <label>✅ Done</label>
                </div>
              </div>

              {/* Intent Pills */}
              <IntentPills
                activeIntent={activeIntent}
                onSelect={setActiveIntent}
                intentCounts={summary?.intent_counts || {}}
              />

              {/* Comment Feed */}
              <CommentFeed
                comments={filteredComments}
                activeTab={activeTab}
                onTabChange={setActiveTab}
                onStatusChange={handleStatusChange}
                loading={adding}
              />
            </div>
          </div>
        </div>
      </div>
    </FBLayout>
  );
};

export default PostDetail;
