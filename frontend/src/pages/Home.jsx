import { useNavigate } from "react-router-dom";
import { MessageSquare, BarChart2, Zap } from "lucide-react";
import "./Home.css";

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="home">
      <div className="home-hero">
        <h1>CommentIQ</h1>
        <p className="home-subtitle">
          Multilingual comment interpretation for social media sellers.
          Understand your customers in Sinhala, Singlish, English and mixed
          language — instantly.
        </p>
        <button className="btn-primary" onClick={() => navigate("/seller")}>
          Open Seller Dashboard
        </button>
      </div>

      <div className="home-features">
        <div className="feature-card">
          <MessageSquare size={32} color="#1877f2" />
          <h3>Smart Classification</h3>
          <p>
            Automatically classifies comments into price inquiries, delivery
            questions, purchase intent and more.
          </p>
        </div>
        <div className="feature-card">
          <Zap size={32} color="#1877f2" />
          <h3>Multilingual Support</h3>
          <p>
            Handles Sinhala, Singlish, English and mixed language comments with
            rule-based and AI-assisted analysis.
          </p>
        </div>
        <div className="feature-card">
          <BarChart2 size={32} color="#1877f2" />
          <h3>Seller Insights</h3>
          <p>
            Get a prioritized view of customer interactions so you never miss a
            potential buyer.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Home;
