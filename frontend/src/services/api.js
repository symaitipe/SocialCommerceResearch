import axios from "axios";
const API_BASE = "http://localhost:8000";

export const analyzeSingle = async (text) => {
  const response = await axios.post("${API_BASE}/analyze/single", { text });
  return response.data;
};

export const analyzeBatch = async (comments) => {
  const response = await axios.post(`${API_BASE}/analyze/batch`, { comments });
  return response.data;
};
