import axios from "axios";

const API_BASE = "http://localhost:8000";

export const fetchPost = async (facebook_url, title) => {
  const response = await axios.post(`${API_BASE}/posts/fetch`, {
    facebook_url,
    title,
  });
  return response.data;
};

export const getAllPosts = async () => {
  const response = await axios.get(`${API_BASE}/posts/`);
  return response.data;
};

export const getPost = async (postId) => {
  const response = await axios.get(`${API_BASE}/posts/${postId}`);
  return response.data;
};

export const getPostComments = async (postId) => {
  const response = await axios.get(`${API_BASE}/posts/${postId}/comments`);
  return response.data;
};

export const getPostSummary = async (postId) => {
  const response = await axios.get(`${API_BASE}/posts/${postId}/summary`);
  return response.data;
};

export const getPostActivity = async (postId) => {
  const response = await axios.get(`${API_BASE}/posts/${postId}/activity`);
  return response.data;
};

export const updateCommentStatus = async (commentId, status) => {
  const response = await axios.patch(
    `${API_BASE}/posts/comments/${commentId}/status`,
    { status },
  );
  return response.data;
};

export const getPostCommentsByIntent = async (postId, intent) => {
  const response = await axios.get(
    `${API_BASE}/posts/${postId}/comments/${intent}`,
  );
  return response.data;
};

export const bulkReplyToComments = async (commentIds, message) => {
  const response = await axios.post(`${API_BASE}/posts/comments/bulk-reply`, {
    comment_ids: commentIds,
    message,
  });
  return response.data;
};
