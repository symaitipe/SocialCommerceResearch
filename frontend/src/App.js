import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import PostAnalysis from "./pages/PostAnalysis";
import CategoryComments from "./pages/CategoryComments";
import OverallInteractions from "./pages/OverallInteractions";
import AllComments from "./pages/AllComments";
import ResearchInsights from "./pages/ResearchInsights";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/post/:postId" element={<PostAnalysis />} />
          <Route
            path="/post/:postId/:intentKey"
            element={<CategoryComments />}
          />
          <Route path="/interactions" element={<OverallInteractions />} />
          <Route path="/comments" element={<AllComments />} />
          <Route path="/research-insights" element={<ResearchInsights />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
