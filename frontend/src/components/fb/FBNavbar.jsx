import {
  Search,
  Home,
  Users,
  Tv,
  ShoppingBag,
  Gamepad2,
  Bell,
  MessageCircle,
  Menu,
} from "lucide-react";
import "./FBNavbar.css";

const FBNavbar = ({ onNotifClick, newCount = 0 }) => {
  return (
    <nav className="fb-navbar">
      {/* Left — Logo + Search */}
      <div className="fb-nav-left">
        <div className="fb-logo">f</div>
        <div className="fb-search">
          <Search size={15} />
          <input placeholder="Search Facebook" />
        </div>
      </div>

      {/* Center — Nav Icons */}
      <div className="fb-nav-center">
        <button className="fb-nav-icon active">
          <Home size={22} />
        </button>
        <button className="fb-nav-icon">
          <Users size={22} />
        </button>
        <button className="fb-nav-icon">
          <Tv size={22} />
        </button>
        <button className="fb-nav-icon">
          <ShoppingBag size={22} />
        </button>
        <button className="fb-nav-icon">
          <Gamepad2 size={22} />
        </button>
      </div>

      {/* Right — Actions */}
      <div className="fb-nav-right">
        <button className="fb-nav-action">
          <Menu size={18} />
        </button>
        <button className="fb-nav-action">
          <MessageCircle size={18} />
        </button>
        <button className="fb-nav-action notif-btn" onClick={onNotifClick}>
          <Bell size={18} />
          {newCount > 0 && <span className="notif-badge">{newCount}</span>}
        </button>
        <div className="fb-avatar">SY</div>
      </div>
    </nav>
  );
};

export default FBNavbar;
