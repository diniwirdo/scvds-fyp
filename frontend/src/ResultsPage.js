import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getResults } from "./api";

function ResultsPage() {
  const { id } = useParams();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getResults(id).then((data) => {
      setResults(data);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="loader">Running GNN Analysis...</div>;
  if (!results) return <p>No results found</p>;

  // Calculate summary stats
  const isSafe = results.total_vulnerabilities === 0;

  return (
    <div className="results-container">
      {/* HEADER SECTION */}
      <div className="results-header">
        <div>
          <h1>Security Analysis Report</h1>
          <p className="file-meta">
            <strong>Target:</strong> {results.filename} <br/>
            <strong>Scanned on:</strong> {new Date(results.uploaded_at).toLocaleString()}
          </p>
        </div>
        <div className={`status-badge ${isSafe ? 'safe' : 'danger'}`}>
          {isSafe ? "✓ SECURE" : "⚠ VULNERABLE"}
        </div>
      </div>

      {/* DASHBOARD SUMMARY */}
      <div className="dashboard-cards">
        <div className="dash-card">
          <h3>Total Issues</h3>
          <span className="value">{results.total_vulnerabilities}</span>
        </div>
        <div className="dash-card">
          <h3>Engine Used</h3>
          <span className="value" style={{fontSize: '1.2rem'}}>GATv2 (GNN)</span>
        </div>
        <div className="dash-card">
          <h3>Scan Time</h3>
          <span className="value" style={{fontSize: '1.2rem'}}>~1.2s</span>
        </div>
      </div>

      {/* RESULTS LIST */}
      {isSafe ? (
        <div className="safe-panel">
          <h2>No Vulnerabilities Detected</h2>
          <p>The GNN model analyzed the AST/CFG structure and found no signs of Access Control or Unchecked Call issues.</p>
        </div>
      ) : (
        <div className="vuln-list">
          <h2>Detected Vulnerabilities</h2>
          {results.vulnerabilities.map((v, i) => (
            <div key={i} className="vuln-card">
              
              {/* CARD HEADER */}
              <div className="vuln-header">
                <h3>{v.type}</h3>
                <div className="badges">
                  <span className={`severity ${v.severity.toLowerCase()}`}>{v.severity}</span>
                  <span className="confidence-badge">{(v.confidence * 100).toFixed(1)}% Match</span>
                </div>
              </div>

              {/* CONFIDENCE BAR */}
              <div className="confidence-bar-bg">
                <div 
                  className={`confidence-bar-fill ${v.severity.toLowerCase()}`}
                  style={{ width: `${v.confidence * 100}%` }}
                ></div>
              </div>

              {/* CODE SNIPPETS (Terminal Style) */}
              <div className="code-snippet-section">
                <h4>Identified Vulnerable Code:</h4>
                <div className="terminal-box">
                  {v.code_snippets ? (
                    v.code_snippets.map((line, idx) => (
                      <div key={idx} className="code-line">{line}</div>
                    ))
                  ) : (
                    <div className="code-line">Line details unavailable.</div>
                  )}
                </div>
              </div>

              {/* RECOMMENDATION */}
              <div className="recommendation-box">
                <h4>How to Fix:</h4>
                <p>{v.recommendation}</p>
              </div>

            </div>
          ))}
        </div>
      )}

      <div className="actions">
        <Link to="/analyze" className="btn">Scan Another Contract</Link>
        <Link to="/history" className="btn btn-outline">View Dashboard</Link>
      </div>
    </div>
  );
}

export default ResultsPage;