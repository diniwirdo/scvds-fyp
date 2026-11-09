import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadFile, analyzeContract } from "./api";
import { FaCloudUploadAlt } from "react-icons/fa";

function AnalyzePage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please choose a .sol file first");
      return;
    }

    setLoading(true);
    setMessage("Uploading contract...");

    try {
      const uploadResult = await uploadFile(file);
      setMessage("Running GATv2 GNN Analysis (this takes a few seconds)...");

      await analyzeContract(uploadResult.contract_id);
      setMessage("Analysis complete! Generating report...");

      setTimeout(() => {
        navigate(`/results/${uploadResult.contract_id}`);
      }, 800);
    } catch (error) {
      setMessage("Error: " + error.message);
      setLoading(false);
    }
  };

  return (
    <div className="analyze-page">
      <h1>Scan Smart Contract</h1>
      <p>Upload a Solidity file (.sol) to detect vulnerabilities using our AI model.</p>

      <div className="upload-box">
        <input
          type="file"
          accept=".sol"
          onChange={handleFileChange}
          disabled={loading}
          id="file-upload"
          style={{ display: "none" }}
        />
        
        {/* Custom Upload Button */}
        <label htmlFor="file-upload" style={{ cursor: "pointer", display: "block", marginBottom: "20px" }}>
          <FaCloudUploadAlt size={50} color="#38bdf8" style={{ marginBottom: "15px" }} />
          <p style={{ color: "#e2e8f0", fontWeight: "bold" }}>
            {file ? file.name : "Click to browse or drag file here"}
          </p>
        </label>

        <button
          className="btn"
          onClick={handleUpload}
          disabled={loading || !file}
        >
          {loading ? "Analyzing..." : "Upload & Analyze"}
        </button>
      </div>

      {message && <div className="message">{message}</div>}

      <div className="info-box">
        <h3>Vulnerability Engine Details</h3>
        <ul>
          <li><strong>Access Control:</strong> Detects functions missing owner restrictions (e.g. missing <code>onlyOwner</code>).</li>
          <li><strong>Unchecked External Call:</strong> Identifies external calls (e.g. <code>.call()</code>) without verifying the return value.</li>
        </ul>
      </div>
    </div>
  );
}

export default AnalyzePage;