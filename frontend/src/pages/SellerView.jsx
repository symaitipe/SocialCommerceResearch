import { useEffect, useState } from "react";
import { useAnalysis } from "../hooks/useAnalysis";
import ProductPost from "../components/ProductPost";
import InsightPanel from "../components/InsightPanel";
import CommentSection from "../components/CommentSection";
import { PlusCircle, RefreshCw } from "lucide-react";
import "./SellerView.css";

const PRODUCT_CATEGORIES = [
  { id: "chair", label: "🪑 Chair" },
  { id: "tinea_herbal", label: "🌿 Tinea Herbal" },
  { id: "general", label: "📦 General" },
];

const SellerView = () => {
  const {
    comments,
    summary,
    loading,
    error,
    fetchComments,
    fetchSummary,
    analyzeComment,
    analyzeBatchComments,
    changeStatus,
  } = useAnalysis();

  const [selectedCategory, setSelectedCategory] = useState("chair");
  const [newComment, setNewComment] = useState("");
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchComments();
    fetchSummary();
  }, []);

  const filteredComments = comments.filter(
    (c) => c.product_category === selectedCategory,
  );

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    setAdding(true);
    await analyzeComment(newComment.trim(), selectedCategory);
    setNewComment("");
    setAdding(false);
  };

  return (
    <div className="seller-view">
      {/* Category Tabs */}
      <div className="category-tabs">
        {PRODUCT_CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            className={`category-tab ${selectedCategory === cat.id ? "active" : ""}`}
            onClick={() => setSelectedCategory(cat.id)}
          >
            {cat.label}
          </button>
        ))}
        <button
          className="refresh-btn"
          onClick={() => {
            fetchComments();
            fetchSummary();
          }}
        >
          <RefreshCw size={16} />
        </button>
      </div>

      <div className="seller-layout">
        {/* Left — Post + Comments */}
        <div className="seller-main">
          <ProductPost category={selectedCategory} />

          {/* Add Comment Box */}
          <div className="add-comment-box">
            <input
              type="text"
              placeholder="Paste a customer comment here..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddComment()}
            />
            <button
              className="add-btn"
              onClick={handleAddComment}
              disabled={adding || loading}
            >
              <PlusCircle size={18} />
              {adding ? "Analyzing..." : "Add & Analyze"}
            </button>
          </div>

          {error && <div className="error-banner">{error}</div>}

          {/* Grouped Comments */}
          <CommentSection
            comments={filteredComments}
            onStatusChange={changeStatus}
            loading={loading}
          />
        </div>

        {/* Right — Insight Panel */}
        <div className="seller-sidebar">
          <InsightPanel summary={summary} comments={filteredComments} />
        </div>
      </div>
    </div>
  );
};

export default SellerView;
