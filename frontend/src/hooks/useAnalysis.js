import { analyzeSingle, analyzeBatch } from "../services/api";
import { useState } from "react";

export const useAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  //analayze an individual comment
  const analyzeComment = async (text) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeSingle(text);
      setResults((prev) => [data, ...prev]);
      return data;
    } catch (error) {
      setError("Failed to analyze comment due to ${error}");
    } finally {
      setLoading(false);
    }
  };

  const analyzeBatchComments = async (comments) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeBatch(comments);
      setResults(data.results);
      setSummary(data.summary);
    } catch (err) {
      setError("Failed to analyze comment due to ${error}");
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setResults([]);
    setSummary(null);
  };

  return {
    results,
    summary,
    loading,
    error,
    analyzeComment,
    analyzeBatchComments,
    clearResults,
  };
};
