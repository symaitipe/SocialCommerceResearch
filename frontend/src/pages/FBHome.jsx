import { useEffect, useState } from "react";
import FBLayout from "../components/fb/FBLayout";
import FBPostCard from "../components/fb/FBPostCard";
import { getCommentsByCategory } from "../services/api";
import "./FBHome.css";

const POSTS = [
  {
    id: "chair",
    name: "Premium Quality Chair",
    emoji: "🪑",
    price: "Rs. 15,000",
    description:
      "🪑 Premium Quality Office & Home Chair — Now Available!\n\nComfortable, durable, and stylish. Available in multiple colors. Perfect for your home or office setup. Limited stock available!\n\n📦 Island wide delivery available\n💬 Comment your order or inbox us for details!",
  },
  {
    id: "tinea_herbal",
    name: "Tinea Herbal Product",
    emoji: "🌿",
    price: "Rs. 1,200",
    description:
      "🌿 Natural Herbal Treatment — Tinea Herbal Product\n\n100% natural ingredients. Safe and effective for all skin types. Trusted by thousands of customers across Sri Lanka.\n\n✅ Fast results\n📦 Delivery island wide\n💬 Comment below to order!",
  },
];

const FBHome = () => {
  const [comments, setComments] = useState({});

  useEffect(() => {
    const fetchAll = async () => {
      const results = {};
      for (const post of POSTS) {
        try {
          results[post.id] = await getCommentsByCategory(post.id);
        } catch {
          results[post.id] = [];
        }
      }
      setComments(results);
    };
    fetchAll();
  }, []);

  return (
    <FBLayout>
      <div className="fb-home">
        {/* Story Row */}
        <div className="fb-stories">
          {["🌅", "🎉", "🌿", "🪑", "😊"].map((emoji, i) => (
            <div key={i} className="fb-story">
              <span>{emoji}</span>
            </div>
          ))}
        </div>

        {/* Posts */}
        {POSTS.map((post) => (
          <FBPostCard
            key={post.id}
            post={post}
            comments={comments[post.id] || []}
            isSeller={true}
          />
        ))}
      </div>
    </FBLayout>
  );
};

export default FBHome;
