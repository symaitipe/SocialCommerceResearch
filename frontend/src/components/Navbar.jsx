import { Link, useLocation } from "react-router-dom";
import { MessageSquare, LayoutDashboard } from "lucide-react";
import "./Navbar.css";

const Navbar = () => {
  const location = useLocation();

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <MessageSquare size={24} />
        <span>CommentIQ</span>
      </div>
      <div className="navbar-links">
        <Link to="/" className={location.pathname === "/" ? "active" : ""}>
          Home
        </Link>
        <Link
          to="/seller"
          className={location.pathname === "/seller" ? "active" : ""}
        >
          <LayoutDashboard size={16} />
          Seller View
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;
