import { useNavigate } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import "./Breadcrumb.css";

// items: [{ label: 'Home', to: '/' }, { label: 'Post-Level Analysis', to: '/post/3' }, { label: 'Purchase Intent' }]
const Breadcrumb = ({ items }) => {
  const navigate = useNavigate();
  return (
    <div className="breadcrumb">
      {items.map((item, i) => (
        <span key={i} className="breadcrumb-item">
          {item.to ? (
            <button
              className="breadcrumb-link"
              onClick={() => navigate(item.to)}
            >
              {item.label}
            </button>
          ) : (
            <span className="breadcrumb-current">{item.label}</span>
          )}
          {i < items.length - 1 && (
            <ChevronRight size={14} className="breadcrumb-sep" />
          )}
        </span>
      ))}
    </div>
  );
};

export default Breadcrumb;
