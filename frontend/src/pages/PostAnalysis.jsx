import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { RefreshCw, ExternalLink, MessageCircle } from "lucide-react";
import {
  getPost,
  getPostSummary,
  getPostActivity,
  fetchPost,
} from "../services/api";
import { INTENT_CONFIG } from "../config/intentConfig";
import Breadcrumb from "../components/Breadcrumb";
import CategoryCard from "../components/CategoryCard";
import ActivityChart from "../components/ActivityChart";
import LanguageDonut from "../components/LanguageDonut";
import "./PostAnalysis.css";

const timeAgo = (ts) => {
  if (!ts) return "never";
  const diff = Date.now() - new Date(ts).getTime();
  const m = Math.floor(diff / 60000);
  const h = Math.floor(diff / 3600000);
  const d = Math.floor(diff / 86400000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  if (h < 24) return `${h}h ago`;
  return `${d}d ago`;
};

const PostAnalysis = () => {
  const { postId } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [summary, setSummary] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [p, s, a] = await Promise.all([
        getPost(postId),
        getPostSummary(postId),
        getPostActivity(postId),
      ]);
      setPost(p);
      setSummary(s);
      setActivity(a);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [postId]);

  const handleSync = async () => {
    if (!post) return;
    setSyncing(true);
    try {
      await fetchPost(post.facebook_url, post.title || "");
      setTimeout(load, 4000);
    } finally {
      setTimeout(() => setSyncing(false), 4000);
    }
  };

  if (loading) return <div className="pa-loading">Loading...</div>;
  if (!post) return <div className="pa-loading">Post not found.</div>;

  const intentCounts = summary?.intent_counts || {};
  const totalComments = summary?.total || 0;

  return (
    <div className="pa-page">
      <Breadcrumb
        items={[{ label: "Home", to: "/" }, { label: "Post-Level Analysis" }]}
      />

      <div className="pa-header">
        <h1>Post-Level Comment Analysis</h1>
        <p>Review customer comments by category</p>
      </div>

      <div className="pa-post-banner">
        <div className="pa-post-thumb">📦</div>
        <div className="pa-post-info">
          <span className="pa-post-title">
            {post.title || post.facebook_url}
          </span>
          <div className="pa-post-meta">
            <span>
              <MessageCircle size={13} /> {totalComments} total comments
            </span>
            <span className="tracking-badge">Tracking</span>
            <span>Last synced {timeAgo(post.last_fetched_at)}</span>
            {post.last_sync_new_count > 0 && (
              <span className="pa-new-badge">
                {post.last_sync_new_count} new since last sync
              </span>
            )}
          </div>
        </div>
        <div className="pa-post-actions">
          <a
            href={post.facebook_url}
            target="_blank"
            rel="noreferrer"
            className="pa-btn-outline"
          >
            <ExternalLink size={14} /> Open Post
          </a>
          <button
            className="pa-btn-primary"
            onClick={handleSync}
            disabled={syncing}
          >
            <RefreshCw size={14} className={syncing ? "spin" : ""} />
            {syncing ? "Syncing..." : "Sync Comments"}
          </button>
        </div>
      </div>

      <div className="pa-section-title">
        <h3>Comment Categories</h3>
        <p>
          Select a category to open its comments. Blue badges show new comments
          from the latest sync.
        </p>
      </div>

      <div className="pa-category-grid">
        {INTENT_CONFIG.map((config) => (
          <CategoryCard
            key={config.key}
            config={config}
            total={intentCounts[config.key] || 0}
            newCount={0}
            onClick={() => navigate(`/post/${postId}/${config.key}`)}
          />
        ))}
      </div>

      <div className="pa-charts-row">
        <div className="pa-chart-card">
          <h4>Comment Activity Over Time</h4>
          <p>Comments received during the last 7 days</p>
          <ActivityChart data={activity} />
        </div>
        <div className="pa-chart-card">
          <h4>Language Distribution</h4>
          <p>Languages detected in this post</p>
          <LanguageDonut
            languageCounts={summary?.language_counts}
            total={totalComments}
          />
        </div>
      </div>
    </div>
  );
};

export default PostAnalysis;
