import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Link2, Lock, Search, Users } from "lucide-react";
import { fetchPost, getAllPosts } from "../services/api";
import { currentUser } from "../config/currentUser";
import PostCard from "../components/PostCard";
import "./Home.css";

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
};

const Home = () => {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [progressMap, setProgressMap] = useState({});
  const eventSourcesRef = useRef({});

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
      Object.values(eventSourcesRef.current).forEach((es) => es.close());
    };
  }, []);

  const trackProgress = (postId) => {
    if (eventSourcesRef.current[postId]) {
      eventSourcesRef.current[postId].close();
    }

    setProgressMap((prev) => ({
      ...prev,
      [postId]: { total: 0, done: false },
    }));

    const es = new EventSource(
      `http://localhost:8000/posts/${postId}/progress`,
    );

    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setProgressMap((prev) => ({ ...prev, [postId]: data }));
      if (data.done) {
        es.close();
        delete eventSourcesRef.current[postId];
        loadPosts();
        setTimeout(() => {
          setProgressMap((prev) => {
            const next = { ...prev };
            delete next[postId];
            return next;
          });
        }, 3000);
      }
    };

    es.onerror = () => {
      es.close();
      delete eventSourcesRef.current[postId];
      loadPosts();
      setProgressMap((prev) => {
        const next = { ...prev };
        delete next[postId];
        return next;
      });
    };

    eventSourcesRef.current[postId] = es;
  };

  const handleFetchNew = async () => {
    if (!url.trim()) {
      setError("Please enter a Facebook post URL or ID.");
      return;
    }
    setError(null);
    setFetching(true);
    try {
      const result = await fetchPost(url.trim(), "");
      setUrl("");
      await loadPosts();
      trackProgress(result.post_id);
    } catch (err) {
      setError("Failed to start fetch. Check backend logs.");
    } finally {
      setFetching(false);
    }
  };

  const handleSync = async (post) => {
    try {
      const result = await fetchPost(post.facebook_url, post.title || "");
      trackProgress(result.post_id);
    } catch (err) {
      setError(`Failed to sync "${post.title || post.facebook_url}".`);
    }
  };

  const filteredPosts = posts.filter((p) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      (p.title || "").toLowerCase().includes(q) ||
      (p.facebook_url || "").toLowerCase().includes(q)
    );
  });

  const totalComments = posts.reduce(
    (sum, p) => sum + (p.total_comments || 0),
    0,
  );

  return (
    <div className="home-page">
      <div className="home-greeting">
        <h1>
          {getGreeting()}
          {currentUser.name ? `, ${currentUser.name}` : ""}
        </h1>
        <p>Monitor and understand your Facebook product conversations.</p>
      </div>

      <div className="analyze-card">
        <div className="analyze-card-header">
          <div className="analyze-fb-icon">f</div>
          <div>
            <h3>Analyze a Facebook post</h3>
            <p>
              Paste a Facebook post URL or Post ID to fetch and classify its
              comments.
            </p>
          </div>
        </div>

        <div className="analyze-input-row">
          <div className="analyze-input-wrap">
            <Link2 size={16} className="analyze-input-icon" />
            <input
              type="text"
              placeholder="Facebook post URL or ID"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleFetchNew()}
              disabled={fetching}
            />
          </div>
          <button onClick={handleFetchNew} disabled={fetching}>
            {fetching ? "Starting..." : "Fetch & Analyze"}
          </button>
        </div>

        <div className="analyze-secure-note">
          <Lock size={13} />
          <span>Comments are processed securely</span>
        </div>

        {error && <div className="error-text">{error}</div>}
      </div>

      <div className="tracked-posts-header">
        <div>
          <h3>Tracked posts</h3>
          <p>
            {posts.length} active post{posts.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="tracked-search">
          <Search size={15} />
          <input
            type="text"
            placeholder="Search by URL or Post ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="posts-list">
        {loading && <p className="empty-text">Loading...</p>}
        {!loading && filteredPosts.length === 0 && (
          <p className="empty-text">
            {posts.length === 0
              ? "No posts yet. Paste a Facebook post URL above to get started."
              : "No posts match your search."}
          </p>
        )}
        {filteredPosts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            progress={progressMap[post.id]}
            onOpen={() => navigate(`/post/${post.id}`)}
            onSync={() => handleSync(post)}
          />
        ))}
      </div>

      {posts.length > 0 && (
        <div className="posts-footer">
          <Users size={15} />
          <span>
            {totalComments} comments monitored across {posts.length} post
            {posts.length !== 1 ? "s" : ""}
          </span>
        </div>
      )}
    </div>
  );
};

export default Home;
