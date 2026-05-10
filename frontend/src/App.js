import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Notifications from "./pages/Notifications";
import PostView from "./pages/PostView";
import "./App.css";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/post/:category" element={<PostView />} />
      </Routes>
    </Router>
  );
}

export default App;
