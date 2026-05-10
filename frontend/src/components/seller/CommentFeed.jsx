import CommentItem from "./CommentItem";
import "./CommentFeed.css";

const TABS = ["new", "pending", "done"];

const CommentFeed = ({
  comments,
  activeTab,
  onTabChange,
  onStatusChange,
  loading,
}) => {
  const getCount = (status) =>
    comments.filter((c) => c.status === status).length;
  const filtered = comments.filter((c) => c.status === activeTab);

  const handleMarkAllReplied = () => {
    filtered.forEach((c) => onStatusChange(c.id, "done"));
  };

  return (
    <div className="comment-feed">
      {/* Tabs */}
      <div className="feed-tabs">
        {TABS.map((tab) => (
          <button
            key={tab}
            className={`feed-tab ${activeTab === tab ? "active" : ""} tab-${tab}`}
            onClick={() => onTabChange(tab)}
          >
            {tab === "new" && "🔴"}
            {tab === "pending" && "🟡"}
            {tab === "done" && "✅"}{" "}
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            <span className="feed-tab-count">{getCount(tab)}</span>
          </button>
        ))}

        {activeTab !== "done" && filtered.length > 1 && (
          <button className="mark-all-btn" onClick={handleMarkAllReplied}>
            ✅ Mark all as replied
          </button>
        )}
      </div>

      {loading && <div className="feed-loading">Analyzing comment...</div>}

      {filtered.length === 0 && !loading && (
        <div className="feed-empty">
          {activeTab === "new" && "🎉 All caught up! No new comments."}
          {activeTab === "pending" && "📭 No pending comments."}
          {activeTab === "done" && "📋 No replied comments yet."}
        </div>
      )}

      <div className="feed-list">
        {filtered.map((comment) => (
          <CommentItem
            key={comment.id}
            result={comment}
            activeTab={activeTab}
            onStatusChange={onStatusChange}
          />
        ))}
      </div>
    </div>
  );
};

export default CommentFeed;
