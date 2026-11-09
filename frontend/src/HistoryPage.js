import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHistory } from "./api";
import { FaShieldAlt, FaExclamationTriangle, FaFileAlt, FaEye } from "react-icons/fa";

function HistoryPage() {
  const [data, setData] = useState({ stats: {}, contracts: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loader">Loading Dashboard Analytics...</div>;

  const { stats, contracts } = data;

  return (
    <div className="dashboard-page">
      <div className="results-header">
        <div>
          <h1>Security Dashboard</h1>
          <p className="file-meta">Overview of your smart contract analysis history.</p>
        </div>
      </div>

      {/* DASHBOARD ANALYTICS CARDS */}
      <div className="dashboard-cards">
        <div className="dash-card">
          <h3><FaFileAlt /> Total Contracts Scanned</h3>
          <span className="value">{stats.total_contracts || 0}</span>
        </div>
        
        <div className="dash-card">
          <h3 style={{ color: '#f87171' }}><FaExclamationTriangle /> Vulnerable Contracts</h3>
          <span className="value" style={{ color: '#f87171' }}>{stats.vulnerable_contracts || 0}</span>
        </div>

        <div className="dash-card">
          <h3 style={{ color: '#38bdf8' }}><FaShieldAlt /> Total Bugs Found</h3>
          <span className="value" style={{ color: '#38bdf8' }}>{stats.total_vulnerabilities || 0}</span>
        </div>
      </div>

      {/* HISTORY TABLE */}
      <h2 style={{ color: '#f8fafc', marginTop: '40px', marginBottom: '10px' }}>Recent Scans</h2>
      
      {contracts.length === 0 ? (
        <div className="safe-panel">
          <h2>No Scans Yet</h2>
          <p>Upload a smart contract to see your security analytics here.</p>
          <Link to="/analyze" className="btn" style={{ marginTop: '20px' }}>Start First Scan</Link>
        </div>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>Contract File</th>
              <th>Date Scanned</th>
              <th>Status</th>
              <th>Issues Found</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {contracts.map((c) => (
              <tr key={c.id}>
                <td style={{ fontWeight: 'bold' }}>{c.filename}</td>
                <td>{new Date(c.uploaded_at).toLocaleString()}</td>
                <td>
                  {c.analyzed ? (
                    c.vuln_count > 0 ? 
                      <span style={{ color: '#f87171', fontWeight: 'bold' }}>⚠ Vulnerable</span> : 
                      <span style={{ color: '#4ade80', fontWeight: 'bold' }}>✓ Secure</span>
                  ) : (
                    <span style={{ color: '#94a3b8' }}>Pending</span>
                  )}
                </td>
                <td>{c.analyzed ? c.vuln_count : '-'}</td>
                <td>
                  <Link to={`/results/${c.id}`} className="btn-outline" style={{ padding: '6px 12px', fontSize: '0.85rem', borderRadius: '6px', display: 'inline-flex', alignItems: 'center', gap: '5px', textDecoration: 'none' }}>
                    <FaEye /> View Report
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default HistoryPage;