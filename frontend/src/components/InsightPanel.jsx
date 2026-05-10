import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import "./InsightPanel.css";

const INTENT_COLORS_MAP = {
  purchase_intent: "#15803d",
  price_inquiry: "#1d4ed8",
  delivery_inquiry: "#92400e",
  product_inquiry: "#7c3aed",
  feedback: "#be185d",
  general: "#64748b",
};

const SENTIMENT_COLORS_MAP = {
  positive: "#15803d",
  negative: "#dc2626",
  neutral: "#64748b",
};

const INTENT_LABELS = {
  purchase_intent: "🛒 Purchase Intent",
  price_inquiry: "💰 Price Inquiry",
  delivery_inquiry: "🚚 Delivery",
  product_inquiry: "📦 Product Inquiry",
  feedback: "⭐ Feedback",
  general: "💬 General",
};

const InsightPanel = ({ summary, comments }) => {
  if (!summary || comments.length === 0) {
    return (
      <div className="insight-panel">
        <h3 className="insight-title">📊 Seller Insights</h3>
        <div className="insight-empty">
          No comments yet. Add comments to see insights.
        </div>
      </div>
    );
  }

  const intentData = Object.entries(summary.intent_counts || {}).map(
    ([key, value]) => ({
      name: INTENT_LABELS[key] || key,
      value,
      color: INTENT_COLORS_MAP[key] || "#64748b",
    }),
  );

  const sentimentData = Object.entries(summary.sentiment_counts || {}).map(
    ([key, value]) => ({
      name: key.charAt(0).toUpperCase() + key.slice(1),
      value,
      color: SENTIMENT_COLORS_MAP[key] || "#64748b",
    }),
  );

  const statusCounts = summary.status_counts || {};
  const total = summary.total || 0;
  const aiCount = comments.filter((c) => c.ai_assisted === 1).length;

  return (
    <div className="insight-panel">
      <h3 className="insight-title">📊 Seller Insights</h3>

      {/* Status Overview */}
      <div className="status-overview">
        <div className="status-stat new">
          <span className="stat-num">{statusCounts.new || 0}</span>
          <span className="stat-label">🔴 New</span>
        </div>
        <div className="status-stat pending">
          <span className="stat-num">{statusCounts.pending || 0}</span>
          <span className="stat-label">🟡 Pending</span>
        </div>
        <div className="status-stat done">
          <span className="stat-num">{statusCounts.done || 0}</span>
          <span className="stat-label">✅ Done</span>
        </div>
      </div>

      {/* Intent Breakdown */}
      <div className="insight-section">
        <h4>Intent Breakdown</h4>
        <ResponsiveContainer width="100%" height={180}>
          <PieChart>
            <Pie
              data={intentData}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={75}
              paddingAngle={3}
              dataKey="value"
            >
              {intentData.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value, name) => [value, name]} />
          </PieChart>
        </ResponsiveContainer>
        <div className="legend">
          {intentData.map((item, i) => (
            <div key={i} className="legend-item">
              <span className="legend-dot" style={{ background: item.color }} />
              <span className="legend-label">{item.name}</span>
              <span className="legend-count">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sentiment Breakdown */}
      <div className="insight-section">
        <h4>Sentiment</h4>
        <ResponsiveContainer width="100%" height={150}>
          <PieChart>
            <Pie
              data={sentimentData}
              cx="50%"
              cy="50%"
              innerRadius={35}
              outerRadius={60}
              paddingAngle={3}
              dataKey="value"
            >
              {sentimentData.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
        <div className="legend">
          {sentimentData.map((item, i) => (
            <div key={i} className="legend-item">
              <span className="legend-dot" style={{ background: item.color }} />
              <span className="legend-label">{item.name}</span>
              <span className="legend-count">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Stats Footer */}
      <div className="insight-footer">
        <div className="footer-stat">
          <span className="footer-num">{total}</span>
          <span className="footer-label">Total Comments</span>
        </div>
        <div className="footer-stat">
          <span className="footer-num">{aiCount}</span>
          <span className="footer-label">AI Assisted</span>
        </div>
        <div className="footer-stat">
          <span className="footer-num">{total - aiCount}</span>
          <span className="footer-label">Rule Based</span>
        </div>
      </div>
    </div>
  );
};

export default InsightPanel;
