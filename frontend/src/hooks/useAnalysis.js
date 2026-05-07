import { useState } from "react";
import {
  analyzeSingle,
  analyzeBatch,
  getAllComments,
  getSummary,
  updateCommentStatus,
} from "../services/api";

export const useAnalysis = () => {
  const [comments, setComments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchComments = async () => {
    setLoading(true);
    try {
      const data = await getAllComments();
      setComments(data);
    } catch (err) {
      setError("Failed to fetch comments.");
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const data = await getSummary();
      setSummary(data);
    } catch (err) {
      setError("Failed to fetch summary.");
    }
  };

  const analyzeComment = async (text, product_category) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeSingle(text, product_category);
      await fetchComments();
      await fetchSummary();
      return data;
    } catch (err) {
      setError("Failed to analyze comment. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const analyzeBatchComments = async (commentsList, product_category) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeBatch(commentsList, product_category);
      await fetchComments();
      await fetchSummary();
      return data;
    } catch (err) {
      setError("Failed to analyze comments. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const changeStatus = async (id, status) => {
    try {
      await updateCommentStatus(id, status);
      setComments((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status } : c)),
      );
      await fetchSummary();
    } catch (err) {
      setError("Failed to update status.");
    }
  };

  return {
    comments,
    summary,
    loading,
    error,
    fetchComments,
    fetchSummary,
    analyzeComment,
    analyzeBatchComments,
    changeStatus,
  };
};
