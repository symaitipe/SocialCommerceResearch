import { useState } from "react";
import CommentItem from "./CommentItem";
import "./CommentSection.css";

const INTENT_GROUPS = [
  {
    key: "purchase_intent",
    label: "Purchase Intent",
    emoji: "🛒",
    priority: 1,
  },
  { key: "price_inquiry", label: "Price Inquiries", emoji: "💰", priority: 2 },
  {
    key: "delivery_inquiry",
    label: "Delivery Questions",
    emoji: "🚚",
    priority: 3,
  },
  {
    key: "product_inquiry",
    label: "Product Inquiries",
    emoji: "📦",
    priority: 4,
  },
  { key: "feedback", label: "Feedback", emoji: "⭐", priority: 5 },
  { key: "general", label: "General", emoji: "💬", priority: 6 },
];

const TABS = ["new", "pending", "done"];

const CommentSection = ({ comments, onStatusChange, loading }) => {
  const [activeTab, setActiveTab] = useState("new");
  const [collapsedGroups, setCollapsedGroups] = useState({});

  const toggleGroup = (key) => {
    setCollapsedGroups((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const filteredByTab = comments.filter((c) => c.status === activeTab);

  const getCountByStatus = (status) =>
    comments.filter((c) => c.status === status).length;

  return (
    <div className="comment-section">
      {/* Status Tabs */}
      <div className="status-tabs">
        {TABS.map((tab) => (
          <button
            key={tab}
            className={`status-tab ${activeTab === tab ? "active" : ""} tab-${tab}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === "new" && "🔴"}
            {tab === "pending" && "🟡"}
            {tab === "done" && "✅"}{" "}
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            <span className="tab-count">{getCountByStatus(tab)}</span>
          </button>
        ))}
      </div>

      {loading && <div className="loading-bar">Analyzing...</div>}

      {/* Grouped by Intent */}
      {INTENT_GROUPS.map((group) => {
        const groupComments = filteredByTab.filter(
          (c) => c.intent === group.key,
        );
        if (groupComments.length === 0) return null;

        const isCollapsed = collapsedGroups[group.key];

        return (
          <div key={group.key} className="intent-group">
            <div
              className="intent-group-header"
              onClick={() => toggleGroup(group.key)}
            >
              <span className="intent-emoji">{group.emoji}</span>
              <span className="intent-label">{group.label}</span>
              <span className="intent-count">{groupComments.length}</span>
              <span className="collapse-icon">{isCollapsed ? "▼" : "▲"}</span>
            </div>

            {!isCollapsed && (
              <div className="intent-group-body">
                {groupComments.map((comment, index) => (
                  <CommentItem
                    key={comment.id}
                    result={comment}
                    index={index}
                    activeTab={activeTab}
                    onStatusChange={onStatusChange}
                  />
                ))}
              </div>
            )}
          </div>
        );
      })}

      {filteredByTab.length === 0 && !loading && (
        <div className="empty-state">
          {activeTab === "new" && "🎉 No new comments — all caught up!"}
          {activeTab === "pending" && "📭 No pending comments."}
          {activeTab === "done" && "📋 No completed comments yet."}
        </div>
      )}
    </div>
  );
};

export default CommentSection;
