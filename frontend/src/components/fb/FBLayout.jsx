import { useState, useEffect } from "react";
import FBNavbar from "./FBNavbar";
import FBLeftSidebar from "./FBLeftSidebar";
import FBRightPanel from "./FBRightPanel";
import { getSummaryByCategory } from "../../services/api";
import "./FBLayout.css";

const POSTS = ["chair", "tinea_herbal"];

const FBLayout = ({ children, showRight = true }) => {
  const [summaries, setSummaries] = useState({});
  const [showNotif, setShowNotif] = useState(false);

  useEffect(() => {
    const fetchSummaries = async () => {
      const results = {};
      for (const id of POSTS) {
        try {
          results[id] = await getSummaryByCategory(id);
        } catch {
          results[id] = null;
        }
      }
      setSummaries(results);
    };
    fetchSummaries();
  }, []);

  const totalNew = POSTS.reduce((acc, id) => {
    return acc + (summaries[id]?.status_counts?.new || 0);
  }, 0);

  return (
    <div className="fb-layout">
      <FBNavbar
        onNotifClick={() => setShowNotif(!showNotif)}
        newCount={totalNew}
      />

      <div className="fb-body">
        <div className="fb-left">
          <FBLeftSidebar />
        </div>

        <div className="fb-center">{children}</div>

        {showRight && (
          <div className="fb-right">
            {showNotif && <FBRightPanel summaries={summaries} />}
          </div>
        )}
      </div>
    </div>
  );
};

export default FBLayout;
