import { useState } from "react";
import { X, Send } from "lucide-react";
import { bulkReplyToComments } from "../services/api";
import "./BulkReplyBar.css";

const BulkReplyBar = ({ selectedIds, onClear, onSent, showToast }) => {
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  const count = selectedIds.length;

  const handleSend = async () => {
    if (!message.trim() || count === 0) return;
    setSending(true);
    setError(null);
    try {
      const data = await bulkReplyToComments(selectedIds, message.trim());
      onSent(selectedIds, data.success_count, data.fail_count);
      setMessage("");
      if (data.fail_count > 0) {
        showToast(
          `✅ Sent to ${data.success_count}, ⚠️ ${data.fail_count} failed`,
        );
      } else {
        showToast(
          `✅ Reply sent to ${data.success_count} comment${data.success_count !== 1 ? "s" : ""}`,
        );
      }
    } catch (e) {
      setError("Network error — check backend");
    } finally {
      setSending(false);
    }
  };

  if (count === 0) return null;

  return (
    <div className="bulk-bar">
      <div className="bulk-bar-inner">
        <div className="bulk-bar-header">
          <span className="bulk-bar-count">{count} selected</span>
          <button className="bulk-bar-clear" onClick={onClear}>
            <X size={14} /> Clear selection
          </button>
        </div>
        <div className="bulk-bar-compose">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={`Type a reply to send to all ${count} selected comment${count !== 1 ? "s" : ""}...`}
            rows={2}
          />
          <button
            className="bulk-bar-send"
            onClick={handleSend}
            disabled={sending || !message.trim()}
          >
            <Send size={15} />
            {sending ? "Sending..." : `Send to ${count}`}
          </button>
        </div>
        {error && <div className="bulk-bar-error">{error}</div>}
      </div>
    </div>
  );
};

export default BulkReplyBar;
