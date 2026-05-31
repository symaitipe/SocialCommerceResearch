import {
  User,
  Users,
  BookMarked,
  Clock,
  ShoppingBag,
  Tv,
  ChevronDown,
} from "lucide-react";
import "./FBLeftSidebar.css";

const MENU_ITEMS = [
  { icon: <User size={20} />, label: "Sahan Yasas", bold: true },
  { icon: <Users size={20} />, label: "Friends" },
  { icon: <BookMarked size={20} />, label: "Saved" },
  { icon: <Clock size={20} />, label: "Memories" },
  { icon: <Users size={20} />, label: "Groups" },
  { icon: <Tv size={20} />, label: "Reels" },
  { icon: <ShoppingBag size={20} />, label: "Marketplace" },
];

const FBLeftSidebar = () => {
  return (
    <div className="fb-left-sidebar">
      {MENU_ITEMS.map((item, i) => (
        <div key={i} className={`fb-menu-item ${item.bold ? "bold" : ""}`}>
          <div className="fb-menu-icon">{item.icon}</div>
          <span>{item.label}</span>
        </div>
      ))}
      <div className="fb-menu-item muted">
        <div className="fb-menu-icon">
          <ChevronDown size={20} />
        </div>
        <span>See more</span>
      </div>

      <div className="fb-sidebar-divider" />

      <div className="fb-sidebar-section">
        <span className="fb-sidebar-title">Your selling posts</span>
        <div className="fb-selling-post">🪑 Premium Quality Chair</div>
        <div className="fb-selling-post">🌿 Tinea Herbal Product</div>
      </div>
    </div>
  );
};

export default FBLeftSidebar;
