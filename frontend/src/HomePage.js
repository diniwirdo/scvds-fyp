import React from "react";
import { Link } from "react-router-dom";
import { FaShieldAlt, FaUpload, FaCogs, FaFileAlt } from "react-icons/fa";

function HomePage() {
  return (
    <div className="home-page">
      <h1>Smart Contract Vulnerability Detector</h1>
      <p>Secure your Web3 applications. Detect Access Control and External Call Vulnerabilities instantly using our Graph Neural Network (GATv2) model.</p>
      
      <Link to="/analyze" className="btn">
        <FaShieldAlt /> Start Security Scan
      </Link>

      <div className="features">
        <div className="feature">
          <h3><FaUpload /> 1. Upload</h3>
          <p>Securely upload your Solidity (.sol) smart contract file to our platform.</p>
        </div>
        <div className="feature">
          <h3><FaCogs /> 2. Analyze</h3>
          <p>Our GNN model builds an AST/CFG graph and scans for hidden logic flaws.</p>
        </div>
        <div className="feature">
          <h3><FaFileAlt /> 3. Report</h3>
          <p>View identified vulnerabilities, confidence scores, and actionable code fixes.</p>
        </div>
      </div>
    </div>
  );
}

export default HomePage;