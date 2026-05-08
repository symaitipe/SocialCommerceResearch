import { ShoppingBag, Tag } from "lucide-react";
import "./ProductPost.css";

const PRODUCT_INFO = {
  chair: {
    name: "Premium Quality Chair",
    emoji: "🪑",
    description:
      "Comfortable and durable chair suitable for office and home use. Available in multiple colors. High quality material with long lasting durability.",
    price: "Rs. 15,000",
    tags: ["Office", "Home", "Premium"],
  },
  tinea_herbal: {
    name: "Tinea Herbal Product",
    emoji: "🌿",
    description:
      "Natural herbal treatment for skin conditions. Made from 100% natural ingredients. Safe and effective for all skin types.",
    price: "Rs. 1,200",
    tags: ["Herbal", "Natural", "Skin Care"],
  },
  general: {
    name: "Product Post",
    emoji: "📦",
    description: "General product category. Add your product details here.",
    price: "Contact for price",
    tags: ["General"],
  },
};

const ProductPost = ({ category }) => {
  const product = PRODUCT_INFO[category] || PRODUCT_INFO.general;

  return (
    <div className="product-post">
      <div className="post-header">
        <div className="page-avatar">🛍️</div>
        <div className="page-info">
          <span className="page-name">Sri Lanka Seller</span>
          <span className="post-time">Social Commerce Post</span>
        </div>
      </div>

      <div className="post-body">
        <div className="product-emoji">{product.emoji}</div>
        <div className="product-details">
          <h2 className="product-name">{product.name}</h2>
          <p className="product-desc">{product.description}</p>
          <div className="product-meta">
            <span className="product-price">
              <Tag size={14} /> {product.price}
            </span>
            <div className="product-tags">
              {product.tags.map((tag) => (
                <span key={tag} className="product-tag">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="post-footer">
        <ShoppingBag size={16} />
        <span>Comment to order or ask questions</span>
      </div>
    </div>
  );
};

export default ProductPost;
