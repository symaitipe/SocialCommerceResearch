import { useRef, useState } from "react";
import { X, Send } from "lucide-react";
import { bulkReplyToComments } from "../services/api";
import "./BulkReplyBar.css";

const MAX_BULK_REPLIES = 25;

const BulkReplyBar = ({ postId, selectedIds, onClear, onSent, showToast }) => {
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const sendingRef = useRef(false);
  const count = selectedIds.length;

  const handleSend = async () => {
    const trimmed = message.trim();
    if (sendingRef.current || !trimmed || count === 0) return;
    if (count > MAX_BULK_REPLIES) {
      setError(`Select at most ${MAX_BULK_REPLIES} comments in one batch.`);
      return;
    }
    if (trimmed.length > 2000) {
      setError("The reply must be 2000 characters or fewer.");
      return;
    }
    if (
      !window.confirm(
        `Send this same reply publicly to ${count} selected Facebook comments?`,
      )
    ) {
      return;
    }

    sendingRef.current = true;
    setSending(true);
    setError(null);

    try {
      const result = await bulkReplyToComments(postId, selectedIds, trimmed);
      await onSent(result);

      if (result.fail_count === 0) {
        setMessage("");
        showToast(
          `Reply sent to ${result.success_count} comment${result.success_count === 1 ? "" : "s"}.`,
        );
      } else {
        const firstFailure = result.results.find((item) => !item.success);
        const uncertain = result.results.some((item) => item.outcome_uncertain);
        const notSaved = result.results.some(
          (item) => item.success && item.db_updated === false,
        );
        const explanation = uncertain
          ? "One request has an uncertain outcome. Check the Facebook post before retrying."
          : firstFailure?.error || "Check the failed comments before retrying.";
        setError(
          `${result.success_count} sent, ${result.fail_count} failed. ${explanation}` +
            (notSaved
              ? " Some local statuses were not updated; refresh before sending again."
              : ""),
        );
        showToast(
          `${result.success_count} sent; ${result.fail_count} failed. Failed comments remain selected.`,
        );
      }

      if (
        result.results.some((item) => item.success && item.db_updated === false)
      ) {
        setError(
          (previous) =>
            `${previous ? previous + " " : ""}Facebook accepted a reply, but its local status was not saved. Refresh and reconcile before sending again.`,
        );
      }
    } catch (exception) {
      const detail = exception.response?.data?.detail;
      const detailText = typeof detail === "string" ? detail : null;
      setError(
        detailText ||
          "Network error. A reply might already have been published. Check Facebook before retrying.",
      );
    } finally {
      sendingRef.current = false;
      setSending(false);
    }
  };

  if (count === 0) return null;

  return (
    <div className="bulk-bar">
      <div className="bulk-bar-inner">
        <div className="bulk-bar-header">
          <span className="bulk-bar-count">{count} selected</span>
          <button
            className="bulk-bar-clear"
            onClick={onClear}
            disabled={sending}
          >
            <X size={14} /> Clear selection
          </button>
        </div>
        <div className="bulk-bar-compose">
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder={`Write one public reply for ${count} selected comments...`}
            rows={2}
            disabled={sending}
          />
          <button
            className="bulk-bar-send"
            onClick={handleSend}
            disabled={
              sending ||
              !message.trim() ||
              count > MAX_BULK_REPLIES ||
              message.trim().length > 2000
            }
          >
            <Send size={15} />
            {sending ? "Sending..." : `Send to ${count}`}
          </button>
        </div>
        {count > MAX_BULK_REPLIES && (
          <div className="bulk-bar-error">Select no more than 25 comments.</div>
        )}
        {error && (
          <div className="bulk-bar-error" role="alert">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default BulkReplyBar;
