import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ChevronLeft,
  ExternalLink,
  Search,
  ChevronUp,
  ChevronDown,
  MessageCircle,
} from "lucide-react";
import {
  getPost,
  getPostCommentsByIntent,
  updateCommentStatus,
} from "../services/api";
import { getIntentConfig, LANGUAGE_LABELS } from "../config/intentConfig";
import Breadcrumb from "../components/Breadcrumb";
import BulkReplyBar from "../components/BulkReplyBar";
import "./CategoryComments.css";

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

const LANG_BADGE = {
  english: "EN",
  singlish: "Singlish",
  sinhala: "Sinhala",
  mixed: "Mixed",
  emoji: "Emoji",
};

const CommentCard = ({
  comment,
  isNew,
  onStatusChange,
  showToast,
  expanded,
  onToggle,
  selected,
  onToggleSelect,
}) => {
  const canReply =
    Boolean(comment.facebook_comment_id) &&
    comment.status !== "replied" &&
    !comment.is_order_request;

  const handleMarkRead = async () => {
    try {
      await onStatusChange(comment.id, "read_not_replied");
      showToast("Marked as read");
    } catch {
      showToast("Could not update comment status");
    }
  };

  return (
    <div
      className={`cc-comment ${isNew ? "new" : ""} ${selected ? "selected" : ""}`}
    >
      <div className="cc-comment-strip" />
      <div className="cc-comment-select">
        <input
          type="checkbox"
          checked={selected}
          disabled={!canReply}
          title={
            canReply
              ? "Select for bulk reply"
              : "No Facebook ID, already replied, or seller template"
          }
          onChange={(event) => {
            event.stopPropagation();
            onToggleSelect(comment.id);
          }}
        />
      </div>
      <div className="cc-comment-body">
        <div className="cc-comment-top" onClick={onToggle}>
          <div className="cc-avatar">
            {(comment.commenter_name || "C").charAt(0).toUpperCase()}
          </div>
          <div className="cc-comment-who">
            <span className="cc-comment-name">
              {comment.commenter_name || "Customer"}
            </span>
            <span className="cc-comment-time">
              {timeAgo(comment.created_at)}
            </span>
          </div>
          <div className="cc-comment-badges">
            <span className="cc-badge intent">
              {getIntentConfig(comment.intent).label}
            </span>
            <span className="cc-badge lang">
              {LANG_BADGE[comment.language] || comment.language}
            </span>
            {isNew && <span className="cc-badge new">NEW</span>}
          </div>
          <div className="cc-comment-quick-actions">
            {comment.facebook_comment_url && (
              <a
                href={comment.facebook_comment_url}
                target="_blank"
                rel="noreferrer"
                className="cc-fb-btn"
                onClick={(event) => event.stopPropagation()}
              >
                <ExternalLink size={13} /> Open on Facebook
              </a>
            )}
            {comment.status !== "replied" && (
              <button
                className="cc-mark-read-btn"
                onClick={(event) => {
                  event.stopPropagation();
                  handleMarkRead();
                }}
              >
                Mark as read
              </button>
            )}
            <span className="cc-expand-icon">
              {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </span>
          </div>
        </div>

        {expanded && (
          <div className="cc-comment-expanded">
            <p className="cc-comment-text">{comment.text}</p>
            <div className="cc-comment-actions">
              {comment.status === "read_not_replied" && (
                <button
                  className="cc-replied-btn"
                  onClick={async () => {
                    try {
                      await onStatusChange(comment.id, "replied");
                      showToast("Marked as replied (no Facebook reply sent)");
                    } catch {
                      showToast("Could not update comment status");
                    }
                  }}
                >
                  Mark replied
                </button>
              )}
              {comment.status === "replied" && (
                <button
                  className="cc-reopen-btn"
                  onClick={async () => {
                    try {
                      await onStatusChange(comment.id, "read_not_replied");
                    } catch {
                      showToast("Could not reopen comment");
                    }
                  }}
                >
                  Reopen
                </button>
              )}
              <span className="cc-select-hint">
                {canReply
                  ? "Select the checkbox to include in a bulk reply"
                  : "Bulk reply unavailable for this comment"}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const CategoryComments = () => {
  const { postId, intentKey } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [search, setSearch] = useState("");
  const [languageFilter, setLanguageFilter] = useState("all");
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [showRead, setShowRead] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const config = getIntentConfig(intentKey);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  };

  const load = async () => {
    setLoading(true);
    try {
      const [p, c] = await Promise.all([
        getPost(postId),
        getPostCommentsByIntent(postId, intentKey),
      ]);
      setPost(p);
      setComments(c);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    setSelectedIds([]);
  }, [postId, intentKey]);

  const handleStatusChange = async (commentId, status) => {
    await updateCommentStatus(commentId, status);
    setComments((previous) =>
      previous.map((comment) =>
        comment.id === commentId ? { ...comment, status } : comment,
      ),
    );
    if (status === "replied") {
      setSelectedIds((previous) => previous.filter((id) => id !== commentId));
    }
  };

  const handleMarkAllRead = async () => {
    const unread = comments.filter((comment) => comment.status === "unread");
    try {
      await Promise.all(
        unread.map((comment) =>
          updateCommentStatus(comment.id, "read_not_replied"),
        ),
      );
      setComments((previous) =>
        previous.map((comment) =>
          comment.status === "unread"
            ? { ...comment, status: "read_not_replied" }
            : comment,
        ),
      );
      showToast(`${unread.length} comments marked as read`);
    } catch {
      showToast(
        "Some statuses could not be updated. Refresh to see the saved results.",
      );
    }
  };

  const toggleSelect = (id) => {
    const comment = comments.find((item) => item.id === id);
    if (
      !comment ||
      !comment.facebook_comment_id ||
      comment.status === "replied" ||
      comment.is_order_request
    ) {
      return;
    }
    setSelectedIds((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id],
    );
  };

  const handleBulkSent = async (data) => {
    const successes = new Set(
      data.results
        .filter((item) => item.success)
        .map((item) => item.comment_id),
    );
    const failures = data.results
      .filter((item) => !item.success && !item.skipped)
      .map((item) => item.comment_id);

    setComments((previous) =>
      previous.map((comment) =>
        successes.has(comment.id) ? { ...comment, status: "replied" } : comment,
      ),
    );
    setSelectedIds(failures);
  };

  const languagesInList = [
    ...new Set(comments.map((comment) => comment.language)),
  ];
  const filtered = comments.filter((comment) => {
    if (languageFilter !== "all" && comment.language !== languageFilter)
      return false;
    if (
      search.trim() &&
      !comment.text.toLowerCase().includes(search.toLowerCase()) &&
      !(comment.commenter_name || "")
        .toLowerCase()
        .includes(search.toLowerCase())
    )
      return false;
    if (unreadOnly && comment.status !== "unread") return false;
    return true;
  });
  const unreadComments = filtered.filter(
    (comment) => comment.status === "unread",
  );
  const readComments = filtered.filter(
    (comment) => comment.status !== "unread",
  );
  const totalCount = comments.length;
  const unreadCount = comments.filter(
    (comment) => comment.status === "unread",
  ).length;
  const newSinceSync =
    post?.last_sync_new_count > 0 ? post.last_sync_new_count : 0;

  if (loading) return <div className="cc-loading">Loading...</div>;
  if (!post) return <div className="cc-loading">Post not found.</div>;

  return (
    <div
      className="cc-page"
      style={{ paddingBottom: selectedIds.length > 0 ? 160 : 40 }}
    >
      <Breadcrumb
        items={[
          { label: "Home", to: "/" },
          { label: "Post-Level Analysis", to: `/post/${postId}` },
          { label: config.label },
        ]}
      />

      <h1 className="cc-title">{config.label} Comments</h1>
      <p className="cc-subtitle">Review customer comments in this category.</p>
      <button className="cc-back" onClick={() => navigate(`/post/${postId}`)}>
        <ChevronLeft size={16} /> Back to Categories
      </button>

      <div className="cc-post-banner">
        <div className="cc-post-thumb">📦</div>
        <div className="cc-post-info">
          <span className="cc-post-title">
            {post.title || post.facebook_url}
          </span>
          <div className="cc-post-meta">
            <span>
              Facebook post · Last synced {timeAgo(post.last_fetched_at)}
            </span>
            <span className="tracking-badge">Tracking</span>
          </div>
        </div>
        <a
          href={post.facebook_url}
          target="_blank"
          rel="noreferrer"
          className="cc-open-btn"
        >
          <ExternalLink size={14} /> Open Post
        </a>
      </div>

      <div className="cc-category-header">
        <div
          className="cc-category-icon"
          style={{ background: `${config.color}1a`, color: config.color }}
        >
          <span>{config.emoji}</span>
        </div>
        <h2>{config.label}</h2>
        <span className="cc-stat-pill">{totalCount} total</span>
        {unreadCount > 0 && (
          <span className="cc-stat-pill unread">{unreadCount} unread</span>
        )}
        {newSinceSync > 0 && (
          <span className="cc-stat-pill new">
            {newSinceSync} new since last sync
          </span>
        )}
        <div className="cc-controls">
          <div className="cc-search">
            <Search size={14} />
            <input
              placeholder="Search comments"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <select
            className="cc-lang-select"
            value={languageFilter}
            onChange={(event) => setLanguageFilter(event.target.value)}
          >
            <option value="all">All languages</option>
            {languagesInList.map((language) => (
              <option key={language} value={language}>
                {LANGUAGE_LABELS[language] || language}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="cc-toolbar">
        <label className="cc-unread-toggle">
          <input
            type="checkbox"
            checked={unreadOnly}
            onChange={(event) => setUnreadOnly(event.target.checked)}
          />
          <span className="cc-toggle-track">
            <span className="cc-toggle-dot" />
          </span>
          Unread only
        </label>
        {unreadComments.length > 0 && (
          <button className="cc-mark-all" onClick={handleMarkAllRead}>
            Mark all as read
          </button>
        )}
      </div>

      {unreadComments.length > 0 && (
        <div className="cc-block">
          <div className="cc-block-header">
            <MessageCircle size={15} />
            <span>Unread Comments</span>
            <span className="cc-block-count">{unreadComments.length}</span>
          </div>
          <p className="cc-block-hint">
            New comments are expanded and highlighted.
          </p>
          {unreadComments.map((comment) => (
            <CommentCard
              key={comment.id}
              comment={comment}
              isNew
              onStatusChange={handleStatusChange}
              showToast={showToast}
              expanded={expandedId === comment.id || true}
              onToggle={() =>
                setExpandedId(expandedId === comment.id ? null : comment.id)
              }
              selected={selectedIds.includes(comment.id)}
              onToggleSelect={toggleSelect}
            />
          ))}
        </div>
      )}

      {!unreadOnly && readComments.length > 0 && (
        <div className="cc-block">
          <button
            className="cc-collapse-header"
            onClick={() => setShowRead(!showRead)}
          >
            <MessageCircle size={15} />
            <span>Previously Read Comments</span>
            <span className="cc-block-count muted">{readComments.length}</span>
            <span className="cc-collapse-hint">Already reviewed comments</span>
            {showRead ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {showRead &&
            readComments.map((comment) => (
              <CommentCard
                key={comment.id}
                comment={comment}
                isNew={false}
                onStatusChange={handleStatusChange}
                showToast={showToast}
                expanded={expandedId === comment.id}
                onToggle={() =>
                  setExpandedId(expandedId === comment.id ? null : comment.id)
                }
                selected={selectedIds.includes(comment.id)}
                onToggleSelect={toggleSelect}
              />
            ))}
        </div>
      )}

      {filtered.length === 0 && (
        <div className="cc-empty">No comments match your current filters.</div>
      )}
      {toast && <div className="cc-toast">{toast}</div>}
      <BulkReplyBar
        postId={postId}
        selectedIds={selectedIds}
        onClear={() => setSelectedIds([])}
        onSent={handleBulkSent}
        showToast={showToast}
      />
    </div>
  );
};

export default CategoryComments;
