import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { fetchPost, getAllPosts } from "../services/api";
import PostCard from "../components/PostCard";
import "./Home.css";

const Home = () => {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState(null);

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
  }, []);

  const handleFetch = async () => {
    if (!url.trim() || !title.trim()) {
      setError(
        "Please enter both the Facebook post URL and a title to verify.",
      );
      return;
    }
    setError(null);
    setFetching(true);
    try {
      const result = await fetchPost(url.trim(), title.trim());
      setUrl("");
      setTitle("");
      // Give the background pipeline a moment, then refresh post list
      setTimeout(loadPosts, 2000);
      alert(
        `Fetch started for post ${result.post_id}. A browser window will open — complete login/CAPTCHA there if needed.`,
      );
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
          placeholder="Facebook post URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <input
          type="text"
          placeholder="Post title (to verify correct post)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <button onClick={handleFetch} disabled={fetching}>
          {fetching ? "Starting..." : "Fetch & Analyze"}
        </button>
        {error && <div className="error-text">{error}</div>}
      </div>

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
