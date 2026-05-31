import "./FBComment.css";

const FBComment = ({ comment }) => {
  return (
    <div className="fb-comment">
      <div className="fb-comment-avatar">
        {comment.author ? comment.author.slice(0, 2).toUpperCase() : "CU"}
      </div>
      <div className="fb-comment-bubble">
        <span className="fb-comment-author">
          {comment.author || `Customer ${comment.id}`}
        </span>
        <p className="fb-comment-text">{comment.text}</p>
        <div className="fb-comment-actions">
          <span>Like</span>
          <span>Reply</span>
          <span className="fb-comment-time">
            {comment.created_at ? timeAgo(comment.created_at) : ""}
          </span>
        </div>
      </div>
    </div>
  );
};

const timeAgo = (timestamp) => {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  const hrs = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m`;
  if (hrs < 24) return `${hrs}h`;
  return `${days}d`;
};

export default FBComment;
