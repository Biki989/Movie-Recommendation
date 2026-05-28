"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";

export default function AdminDashboard() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState(null);
  const [trainStatus, setTrainStatus] = useState({ running: false, message: "idle", progress: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Route protection: Block non-admins
  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push("/login");
      } else if (!user.is_admin) {
        router.push("/recommendations");
      }
    }
  }, [user, authLoading]);

  // Fetch admin dashboard stats & curves on load
  useEffect(() => {
    if (!user || !user.is_admin) return;
    
    async function fetchDashboardData() {
      try {
        const [statsResp, histResp] = await Promise.all([
          fetch("http://localhost:8000/api/admin/stats", { credentials: "include" }),
          fetch("http://localhost:8000/api/admin/training-history", { credentials: "include" })
        ]);
        
        if (statsResp.status === 200) {
          const statsData = await statsResp.json();
          setStats(statsData);
        }
        if (histResp.status === 200) {
          const histData = await histResp.json();
          setHistory(histData);
        }
      } catch (e) {
        setError("Failed to load admin statistics.");
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, [user]);

  // Handle active progress polling when a training job is running
  useEffect(() => {
    if (!trainStatus.running) return;

    const interval = setInterval(async () => {
      try {
        const resp = await fetch("http://localhost:8000/api/admin/training-status", { credentials: "include" });
        if (resp.status === 200) {
          const statusData = await resp.json();
          setTrainStatus(statusData);
          
          if (!statusData.running) {
            // Training finished! Refresh stats and curves
            const [statsResp, histResp] = await Promise.all([
              fetch("http://localhost:8000/api/admin/stats", { credentials: "include" }),
              fetch("http://localhost:8000/api/admin/training-history", { credentials: "include" })
            ]);
            if (statsResp.status === 200) setStats(await statsResp.json());
            if (histResp.status === 200) setHistory(await histResp.json());
            clearInterval(interval);
          }
        }
      } catch (e) {}
    }, 1000);

    return () => clearInterval(interval);
  }, [trainStatus.running]);

  const handleRetrainSubmit = async () => {
    setError("");
    try {
      const resp = await fetch("http://localhost:8000/api/admin/retrain", {
        method: "POST",
        credentials: "include"
      });
      const data = await resp.json();
      if (resp.status === 200 && data.success) {
        setTrainStatus({ running: true, message: "Model retraining queued...", progress: 5 });
      } else {
        setError(data.detail || "Training trigger failed.");
      }
    } catch (e) {
      setError("Network request failed.");
    }
  };

  // Helper function to render a gorgeous inline SVG line chart
  const renderSVGChart = (dataList, color, title) => {
    if (!dataList || dataList.length === 0) {
      return (
        <div style={{ color: "var(--text-dimmed)", fontSize: "0.85rem", textAlign: "center", padding: "3rem 0" }}>
          No historical data points logged.
        </div>
      );
    }

    const width = 450;
    const height = 200;
    const padding = 30;

    const minVal = Math.min(...dataList);
    const maxVal = Math.max(...dataList);
    const valRange = maxVal - minVal || 1.0;

    const points = dataList.map((val, index) => {
      const x = padding + (index / (dataList.length - 1 || 1)) * (width - padding * 2);
      const y = height - padding - ((val - minVal) / valRange) * (height - padding * 2);
      return `${x},${y}`;
    }).join(" ");

    return (
      <div style={{ position: "relative" }}>
        <h4 style={{ fontSize: "0.95rem", color: "var(--text-muted)", marginBottom: "0.5rem", textAlign: "center" }}>{title}</h4>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", border: "1px solid var(--border-light)", borderRadius: "8px", background: "rgba(0,0,0,0.2)" }}>
          {/* Grid lines */}
          <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="rgba(255,255,255,0.05)" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="rgba(255,255,255,0.05)" />
          
          {/* Axis Labels */}
          <text x={padding - 5} y={padding + 5} fill="var(--text-dimmed)" fontSize="10" textAnchor="end">{maxVal.toFixed(2)}</text>
          <text x={padding - 5} y={height - padding} fill="var(--text-dimmed)" fontSize="10" textAnchor="end">{minVal.toFixed(2)}</text>
          <text x={width / 2} y={height - 5} fill="var(--text-dimmed)" fontSize="10" textAnchor="middle">Epochs ({dataList.length})</text>

          {/* Line Path */}
          <polyline
            fill="none"
            stroke={color}
            strokeWidth="3"
            points={points}
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Dots on data points */}
          {dataList.map((val, index) => {
            const x = padding + (index / (dataList.length - 1 || 1)) * (width - padding * 2);
            const y = height - padding - ((val - minVal) / valRange) * (height - padding * 2);
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="4"
                fill="#fff"
                stroke={color}
                strokeWidth="2"
              />
            );
          })}
        </svg>
      </div>
    );
  };

  if (authLoading || !user || !user.is_admin) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "8rem 0" }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ borderBottom: "1px solid var(--border-light)", paddingBottom: "2rem", marginBottom: "2.5rem" }}>
        <span style={{ fontSize: "0.75rem", background: "rgba(245, 197, 24, 0.15)", color: "var(--accent)", border: "1px solid var(--accent)", padding: "0.2rem 0.5rem", borderRadius: "4px", fontWeight: 700, textTransform: "uppercase", display: "inline-block", marginBottom: "0.5rem" }}>
          Root System Administrator
        </span>
        <h1 style={{ fontSize: "2.8rem", fontWeight: 800 }}>⚙️ System Control Center</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Monitor system metrics, retrain PyTorch embedding weights, and inspect model learning performance
        </p>
      </div>

      {error && (
        <div style={{ background: "rgba(229, 9, 20, 0.1)", border: "1px solid var(--primary)", color: "#ff8080", padding: "1rem", borderRadius: "10px", marginBottom: "2rem" }}>
          ⚠️ {error}
        </div>
      )}

      {/* ── DATABASE STATS SECTION ────────────────────────────────────────────── */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div>
              <div className="stat-val">{stats.total_users}</div>
              <div className="stat-label">Registered Users</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⭐</div>
            <div>
              <div className="stat-val">{stats.total_ratings}</div>
              <div className="stat-label">Total Ratings</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">❤️</div>
            <div>
              <div className="stat-val">{stats.total_bookmarks}</div>
              <div className="stat-label">Total Bookmarks</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🧠</div>
            <div>
              <div className="stat-val" style={{ color: stats.model_ready ? "#00ff88" : "#ff4040" }}>
                {stats.model_ready ? "Online" : "Offline"}
              </div>
              <div className="stat-label">AI Engine Model</div>
            </div>
          </div>
        </div>
      )}

      {/* ── RETRAINING CONTROL & MONITOR PANEL ─────────────────────────────────── */}
      <div className="sidebar-layout" style={{ marginTop: 0 }}>
        {/* Left Column: Retraining controls */}
        <div className="glass-panel" style={{ height: "fit-content" }}>
          <h3 style={{ fontSize: "1.4rem", fontWeight: 800, marginBottom: "1rem" }}>🤖 PyTorch NCF Training</h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "2rem" }}>
            Re-fits user & movie embedding arrays. Retraining is safe, non-blocking, and processes asynchronously inside the FastAPI worker threads.
          </p>

          {trainStatus.running ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", fontWeight: 700, marginBottom: "0.4rem" }}>
                <span>{trainStatus.message}</span>
                <span style={{ color: "var(--primary)" }}>{trainStatus.progress}%</span>
              </div>
              <div className="progress-container" style={{ height: "10px", marginBottom: "1rem" }}>
                <div className="progress-bar" style={{ width: `${trainStatus.progress}%` }}></div>
              </div>
              <span style={{ fontSize: "0.75rem", color: "var(--text-dimmed)" }}>
                * Standard computation takes 20-40 seconds on local CPU. Please wait.
              </span>
            </div>
          ) : (
            <button className="btn btn-primary" style={{ width: "100%", padding: "1rem" }} onClick={handleRetrainSubmit}>
              ⚡ Run Retraining Now
            </button>
          )}
        </div>

        {/* Right Column: Historical loss and MAE graphs */}
        <div className="glass-panel">
          <h3 style={{ fontSize: "1.4rem", fontWeight: 800, marginBottom: "1.5rem" }}>📈 Learning Curves (History)</h3>
          
          {history ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "2rem" }}>
              {history.loss && history.loss.length > 0 ? (
                <>
                  {renderSVGChart(history.loss, "var(--primary)", "Train Loss (MSE)")}
                  {renderSVGChart(history.mae, "#00d4aa", "Mean Absolute Error (MAE)")}
                </>
              ) : (
                <div style={{ gridColumn: "span 2", textAlign: "center", color: "var(--text-dimmed)", padding: "4rem 0" }}>
                  📊 No historical metrics parsed. Run the first retraining to generate charts!
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: "flex", justifyContent: "center", padding: "4rem 0" }}>
              <div className="spinner"></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
