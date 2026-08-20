import { Bell } from "lucide-react";
import "./TopBar.css";

const TopBar = ({ notifCount = 0, userName = "Sahan" }) => {
  return (
    <div className="topbar">
      <button className="topbar-bell" title="Notifications">
        <Bell size={20} />
        {notifCount > 0 && (
          <span className="topbar-bell-badge">{notifCount}</span>
        )}
      </button>
      <div className="topbar-avatar" title={userName}>
        {userName.charAt(0).toUpperCase()}
      </div>
    </div>
  );
};

export default TopBar;
