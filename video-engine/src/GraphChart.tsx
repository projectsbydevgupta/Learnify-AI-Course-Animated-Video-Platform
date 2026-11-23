import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

interface GraphChartProps {
  visual_data?: {
    chart_type?: string;
    title?: string;
    x_label?: string;
    y_label?: string;
    show_line?: boolean;
    points?: Array<{ x: number; y: number; label?: string }>;
    bars?: Array<{ label: string; value: number; color?: string }>;
    nodes?: Array<{ label: string; status?: "active" | "neutral" | "target" }>;
    flow_steps?: Array<{ title: string; desc: string }>;
    metrics?: Array<{ label: string; value: string }>;
  };
  text?: string;
}

export const GraphChart: React.FC<GraphChartProps> = ({ visual_data, text }) => {
  const frame = useCurrentFrame();

  // Smooth entry interpolation
  const progress = interpolate(frame, [0, 25], [0, 1], {
    extrapolateRight: "clamp",
  });

  const chartType = visual_data?.chart_type || "scatter_trend";
  const title = visual_data?.title || text || "Visual Concept Model";
  const xLabel = visual_data?.x_label || "Input Feature (X)";
  const yLabel = visual_data?.y_label || "Target / Error (Y)";
  const showLine = visual_data?.show_line !== false;

  // Default points for scatter/trend if not provided
  const points = visual_data?.points || [
    { x: 120, y: 380 },
    { x: 240, y: 330 },
    { x: 360, y: 280 },
    { x: 480, y: 240 },
    { x: 600, y: 180 },
    { x: 720, y: 130 },
    { x: 840, y: 90 },
  ];

  // Default comparison bars if requested
  const bars = visual_data?.bars || [
    { label: "Linear Search O(N)", value: 85, color: "#f43f5e" },
    { label: "Binary Search O(log N)", value: 20, color: "#10b981" },
    { label: "Indexed Hash O(1)", value: 10, color: "#06b6d4" },
  ];

  return (
    <div
      style={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "#f8fafc",
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
      }}
    >
      {/* Chart Title Header */}
      <div style={{ textAlign: "center", marginBottom: "30px" }}>
        <h2
          style={{
            fontSize: "44px",
            fontWeight: 800,
            color: "#38bdf8",
            letterSpacing: "-0.5px",
            margin: 0,
            textShadow: "0 0 25px rgba(56, 189, 248, 0.4)",
          }}
        >
          {title}
        </h2>
        {text && text !== title && (
          <p style={{ fontSize: "24px", color: "#94a3b8", margin: "8px 0 0 0" }}>
            {text}
          </p>
        )}
      </div>

      {/* Render Chart Mode 1: Scatter & Regression / Trendline */}
      {chartType === "scatter_trend" && (
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.8)",
            border: "2px solid rgba(56, 189, 248, 0.25)",
            borderRadius: "24px",
            padding: "40px 60px",
            boxShadow: "0 30px 60px -15px rgba(0, 0, 0, 0.7)",
            position: "relative",
          }}
        >
          <svg width="960" height="460" viewBox="0 0 960 460" style={{ overflow: "visible" }}>
            <defs>
              <linearGradient id="lineGrad" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="100%" stopColor="#818cf8" />
              </linearGradient>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Grid Lines */}
            <line x1="100" y1="90" x2="880" y2="90" stroke="#1e293b" strokeDasharray="6" strokeWidth="2" />
            <line x1="100" y1="190" x2="880" y2="190" stroke="#1e293b" strokeDasharray="6" strokeWidth="2" />
            <line x1="100" y1="290" x2="880" y2="290" stroke="#1e293b" strokeDasharray="6" strokeWidth="2" />
            <line x1="100" y1="390" x2="880" y2="390" stroke="#334155" strokeWidth="3" />

            {/* Y Axis */}
            <line x1="100" y1="50" x2="100" y2="390" stroke="#334155" strokeWidth="3" />

            {/* Data Points */}
            {points.map((pt, i) => (
              <g key={i}>
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={12 * progress}
                  fill="#38bdf8"
                  filter="url(#glow)"
                  opacity={progress}
                />
                <circle cx={pt.x} cy={pt.y} r={5 * progress} fill="#ffffff" />
              </g>
            ))}

            {/* Trendline */}
            {showLine && (
              <line
                x1="80"
                y1="410"
                x2="890"
                y2="70"
                stroke="url(#lineGrad)"
                strokeWidth="6"
                strokeLinecap="round"
                filter="url(#glow)"
                opacity={progress}
              />
            )}

            {/* Axis Labels */}
            <text x="490" y="440" fill="#94a3b8" fontSize="22" fontWeight="600" textAnchor="middle">
              {xLabel} →
            </text>
            <text
              x="-220"
              y="40"
              fill="#94a3b8"
              fontSize="22"
              fontWeight="600"
              transform="rotate(-90)"
              textAnchor="middle"
            >
              ↑ {yLabel}
            </text>
          </svg>

          {/* Bottom Metric Pill */}
          <div
            style={{
              marginTop: "24px",
              display: "flex",
              justifyContent: "space-around",
              backgroundColor: "rgba(30, 41, 59, 0.6)",
              borderRadius: "16px",
              padding: "16px 30px",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              fontSize: "20px",
              color: "#cbd5e1",
            }}
          >
            <span>
              🎯 <strong style={{ color: "#38bdf8" }}>Goal:</strong> Minimize Residual Error
            </span>
            <span>
              📈 <strong style={{ color: "#818cf8" }}>Model:</strong> Optimal Fit Line
            </span>
            <span>
              ⚡ <strong style={{ color: "#34d399" }}>Convergence:</strong> High Accuracy
            </span>
          </div>
        </div>
      )}

      {/* Render Chart Mode 2: Bar Comparison (e.g. Algorithmic Efficiency) */}
      {chartType === "bar_comparison" && (
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.8)",
            border: "2px solid rgba(129, 140, 248, 0.25)",
            borderRadius: "24px",
            padding: "50px 70px",
            width: "1000px",
            boxShadow: "0 30px 60px -15px rgba(0, 0, 0, 0.7)",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
            {bars.map((bar, idx) => {
              const barWidthPercent = bar.value * progress;
              return (
                <div key={idx} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "22px",
                      fontWeight: 600,
                      color: "#e2e8f0",
                    }}
                  >
                    <span>{bar.label}</span>
                    <span style={{ color: bar.color || "#38bdf8", fontWeight: 700 }}>
                      {Math.round(bar.value)} ops
                    </span>
                  </div>
                  <div
                    style={{
                      width: "100%",
                      height: "36px",
                      backgroundColor: "rgba(30, 41, 59, 0.8)",
                      borderRadius: "12px",
                      overflow: "hidden",
                      border: "1px solid rgba(255, 255, 255, 0.05)",
                    }}
                  >
                    <div
                      style={{
                        width: `${barWidthPercent}%`,
                        height: "100%",
                        backgroundColor: bar.color || "#38bdf8",
                        borderRadius: "12px",
                        boxShadow: `0 0 20px ${bar.color || "#38bdf8"}88`,
                        transition: "width 0.2s ease-out",
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Render Chart Mode 3: Tree / Pipeline Flow */}
      {chartType === "tree_split" && (
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.8)",
            border: "2px solid rgba(16, 185, 129, 0.25)",
            borderRadius: "24px",
            padding: "50px 60px",
            width: "980px",
            boxShadow: "0 30px 60px -15px rgba(0, 0, 0, 0.7)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-around",
              alignItems: "center",
              gap: "20px",
            }}
          >
            <div
              style={{
                backgroundColor: "rgba(30, 41, 59, 0.9)",
                border: "2px solid #38bdf8",
                borderRadius: "18px",
                padding: "24px 30px",
                textAlign: "center",
                flex: 1,
                boxShadow: "0 0 25px rgba(56, 189, 248, 0.3)",
              }}
            >
              <div style={{ fontSize: "28px", fontWeight: 700, color: "#38bdf8" }}>Step 1</div>
              <div style={{ fontSize: "20px", color: "#cbd5e1", marginTop: "8px" }}>
                Split / Evaluate Condition
              </div>
            </div>

            <div style={{ fontSize: "36px", color: "#64748b" }}>➔</div>

            <div
              style={{
                backgroundColor: "rgba(30, 41, 59, 0.9)",
                border: "2px solid #818cf8",
                borderRadius: "18px",
                padding: "24px 30px",
                textAlign: "center",
                flex: 1,
                boxShadow: "0 0 25px rgba(129, 140, 248, 0.3)",
              }}
            >
              <div style={{ fontSize: "28px", fontWeight: 700, color: "#818cf8" }}>Step 2</div>
              <div style={{ fontSize: "20px", color: "#cbd5e1", marginTop: "8px" }}>
                Eliminate 50% Search Space
              </div>
            </div>

            <div style={{ fontSize: "36px", color: "#64748b" }}>➔</div>

            <div
              style={{
                backgroundColor: "rgba(30, 41, 59, 0.9)",
                border: "2px solid #34d399",
                borderRadius: "18px",
                padding: "24px 30px",
                textAlign: "center",
                flex: 1,
                boxShadow: "0 0 25px rgba(52, 211, 153, 0.3)",
              }}
            >
              <div style={{ fontSize: "28px", fontWeight: 700, color: "#34d399" }}>Step 3</div>
              <div style={{ fontSize: "20px", color: "#cbd5e1", marginTop: "8px" }}>
                Reach Target Solution
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};