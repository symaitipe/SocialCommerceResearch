import { ChevronRight } from "lucide-react";
import "./CategoryCard.css";

const CategoryCard = ({ config, total, newCount, onClick }) => {
  if (total === 0) return null;

  return (
    <button className="category-card" onClick={onClick}>
      <div
        className="category-card-icon"
        style={{ background: `${config.color}1a`, color: config.color }}
      >
        <span>{config.emoji}</span>
      </div>
      <div className="category-card-body">
        <span className="category-card-label">{config.label}</span>
        <div className="category-card-numbers">
          <span className="category-card-total">{total}</span>
          {newCount > 0 && (
            <span className="category-card-new">{newCount} new</span>
          )}
        </div>
      </div>
      <ChevronRight size={16} className="category-card-arrow" />
    </button>
  );
};

export default CategoryCard;
