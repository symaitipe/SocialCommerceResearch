import axios from "axios";
const API_BASE = "http://localhost:8000";

export const analyzeSingle = async (text, product_category = "general") => {
  const response = await axios.post("${API_BASE}/analyze/single", { text });
  return response.data;
};

export const analyzeBatch = async (comments, product_category = "general") => {
  const response = await axios.post(`${API_BASE}/analyze/batch`, { comments });
  return response.data;
};

export const getAllComments = async () => {
  const response = await axios.get(`${API_BASE}/comments/`);
  return response.data;
};

export const getSummary = async () => {
  const response = await axios.get(`${API_BASE}/comments/summary`);
  return response.data;
};

export const updateCommentStatus = async (id, status) => {
  const response = axios.patch(`${API_BASE}/comments/${id}/status`, { status });
  return response.data;
};
