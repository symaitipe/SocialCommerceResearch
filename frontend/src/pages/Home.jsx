import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { fetchPost, getAllPosts } from "../services/api";
import PostCard from "../components/PostCard";
import "./Home.css";

const Home = () => {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null);
  const eventSourceRef = useRef(null);

  const loadPosts = async () => {
    setLoading(true);
    try {
      const data = await getAllPosts();
      setPosts(data);
    } catch (err) {
      setError("Could not load posts. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPosts();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const startProgressTracking = (postId) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setProgress({ status: "starting", total: 0, done: false });

    const es = new EventSource(
      `http://localhost:8000/posts/${postId}/progress`,
    );

    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setProgress(data);
      if (data.done) {
        es.close();
        loadPosts();
        setTimeout(() => setProgress(null), 3000);
      }
    };

    es.onerror = () => {
      es.close();
      loadPosts();
      setProgress(null);
    };

    eventSourceRef.current = es;
  };

  const handleFetch = async () => {
    if (!url.trim()) {
      setError("Please enter a Facebook post URL.");
      return;
    }
    setError(null);
    setFetching(true);
    try {
      const result = await fetchPost(url.trim(), "");
      setUrl("");
      startProgressTracking(result.post_id);
    } catch (err) {
      setError("Failed to start fetch. Check backend logs.");
    } finally {
      setFetching(false);
    }
  };

  return (
    <div className="home-page">
      <div className="home-header">
        <h1>🔍 CommentIQ</h1>
        <p>Paste a Facebook post link to analyze its comments</p>
      </div>

      <div className="fetch-box">
        <input
          type="text"
          placeholder="Facebook post URL or Post ID"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleFetch()}
          disabled={fetching}
        />
        <button onClick={handleFetch} disabled={fetching || !!progress}>
          {fetching ? "Starting..." : "Fetch & Analyze"}
        </button>
        {error && <div className="error-text">{error}</div>}
      </div>

      {/* Progress Bar */}
      {progress && (
        <div className="progress-box">
          <div className="progress-header">
            <span>
              {progress.done
                ? `✅ Done! ${progress.total} comments analyzed`
                : `⏳ Fetching and analyzing comments...`}
            </span>
            {!progress.done && (
              <span className="progress-count">
                {progress.total > 0
                  ? `${progress.total} fetched`
                  : "Starting..."}
              </span>
            )}
          </div>
          <div className="progress-bar-track">
            <div
              className={`progress-bar-fill ${progress.done ? "done" : "animating"}`}
            />
          </div>
          {progress.done && progress.new_count > 0 && (
            <div className="progress-new">
              +{progress.new_count} new comments added
            </div>
          )}
        </div>
      )}

      <div className="posts-list">
        <h3>Tracked Posts</h3>
        {loading && <p>Loading...</p>}
        {!loading && posts.length === 0 && (
          <p className="empty-text">
            No posts yet. Paste a Facebook post URL above to get started.
          </p>
        )}
        {posts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            onClick={() => navigate(`/post/${post.id}`)}
          />
        ))}
      </div>
    </div>
  );
};

export default Home;
