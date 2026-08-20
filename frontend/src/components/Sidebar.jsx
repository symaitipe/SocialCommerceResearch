import { useNavigate, useLocation } from "react-router-dom";
import {
  Home as HomeIcon,
  FileText,
  BarChart3,
  MessageCircle,
  ShieldCheck,
} from "lucide-react";
import "./Sidebar.css";

const NAV_ITEMS = [
  { to: "/", icon: HomeIcon, label: "Home", exact: true },
  {
    to: "/",
    icon: FileText,
    label: "Post-Level Analysis",
    matchPrefix: "/post",
  },
  { to: "/interactions", icon: BarChart3, label: "Overall Interactions" },
  { to: "/comments", icon: MessageCircle, label: "Comments" },
];

const ADMIN_ITEMS = [
  { to: "/research-insights", icon: ShieldCheck, label: "Research Insights" },
];

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (item) => {
    if (item.matchPrefix) return location.pathname.startsWith(item.matchPrefix);
    if (item.exact) return location.pathname === item.to;
    return location.pathname.startsWith(item.to) && item.to !== "/";
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand" onClick={() => navigate("/")}>
        <div className="sidebar-brand-icon">SS</div>
        <div>
          <div className="sidebar-brand-name">SocialSell</div>
          <div className="sidebar-brand-sub">Advisor</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.label}
            className={`sidebar-link ${isActive(item) ? "active" : ""}`}
            onClick={() => navigate(item.to)}
          >
            <item.icon size={18} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-divider" />
      <div className="sidebar-section-label">Admin Only</div>
      <nav className="sidebar-nav">
        {ADMIN_ITEMS.map((item) => (
          <button
            key={item.label}
            className={`sidebar-link admin ${location.pathname === item.to ? "active" : ""}`}
            onClick={() => navigate(item.to)}
          >
            <item.icon size={18} />
            <span>{item.label}</span>
            <span className="sidebar-admin-badge">Admin</span>
          </button>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
