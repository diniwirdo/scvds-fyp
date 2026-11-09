import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import HomePage from "./HomePage";
import AnalyzePage from "./AnalyzePage";
import ResultsPage from "./ResultsPage";
import HistoryPage from "./HistoryPage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <nav className="navbar">
        <h1>SCVDS</h1>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/analyze">Analyze</Link>
          <Link to="/history">History</Link>
        </div>
      </nav>
      <div className="container">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="/results/:id" element={<ResultsPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;