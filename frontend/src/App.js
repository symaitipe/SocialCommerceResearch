import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import FBHome from "./pages/FBHome";
import PostDetail from "./pages/PostDetail";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<FBHome />} />
        <Route path="/post/:category" element={<PostDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
