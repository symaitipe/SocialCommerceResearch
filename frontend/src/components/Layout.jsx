import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import "./Layout.css";

const Layout = ({ children }) => {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-content">
        <TopBar />
        <div className="app-content-inner">{children}</div>
      </div>
    </div>
  );
};

export default Layout;
