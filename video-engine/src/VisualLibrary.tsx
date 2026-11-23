import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

// =========================================================================
// 1. ARRAY & MEMORY VISUALIZER (For Arrays, Binary Search, Sequences)
// =========================================================================
export interface ArrayVisualProps {
  visual_data?: {
    title?: string;
    items?: Array<{ index: number; value: string | number; address?: string; status?: "normal" | "active" | "target" | "eliminated" }>;
    pointers?: Array<{ label: string; index: number; color?: string }>;
    target?: string | number;
    explanation?: string;
  };
  text?: string;
}

export const ArrayMemoryVisual: React.FC<ArrayVisualProps> = ({ visual_data, text }) => {
  const frame = useCurrentFrame();

  const progress = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const pulse = Math.sin(frame * 0.15) * 4;

  const title = visual_data?.title || text || "Contiguous Sequence in Memory";
  const items = visual_data?.items || [
    { index: 0, value: 12, address: "0x1000", status: "eliminated" },
    { index: 1, value: 24, address: "0x1004", status: "eliminated" },
    { index: 2, value: 37, address: "0x1008", status: "active" },
    { index: 3, value: 45, address: "0x100C", status: "target" },
    { index: 4, value: 68, address: "0x1010", status: "active" },
    { index: 5, value: 89, address: "0x1014", status: "normal" },
    { index: 6, value: 99, address: "0x1018", status: "normal" },
  ];

  const pointers = visual_data?.pointers || [
    { label: "Low", index: 2, color: "#38bdf8" },
    { label: "Mid", index: 3, color: "#f59e0b" },
    { label: "High", index: 4, color: "#ec4899" },
  ];

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", color: "#f8fafc" }}>
      <h2 style={{ fontSize: "44px", fontWeight: 800, color: "#38bdf8", marginBottom: "35px", letterSpacing: "-0.5px" }}>
        {title}
      </h2>

      {/* Main Memory Ribbon Card */}
      <div
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.85)",
          border: "2px solid rgba(56, 189, 248, 0.3)",
          borderRadius: "24px",
          padding: "50px 60px",
          boxShadow: "0 30px 60px rgba(0, 0, 0, 0.7)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "24px",
        }}
      >
        <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
          {items.map((item, idx) => {
            const isTarget = item.status === "target";
            const isEliminated = item.status === "eliminated";
            const isActive = item.status === "active";

            let borderColor = "rgba(255, 255, 255, 0.15)";
            let bgColor = "rgba(30, 41, 59, 0.8)";
            let textColor = "#f8fafc";

            if (isTarget) {
              borderColor = "#10b981";
              bgColor = "rgba(16, 185, 129, 0.25)";
              textColor = "#34d399";
            } else if (isEliminated) {
              borderColor = "rgba(100, 116, 139, 0.2)";
              bgColor = "rgba(15, 23, 42, 0.5)";
              textColor = "#64748b";
            } else if (isActive) {
              borderColor = "#38bdf8";
              bgColor = "rgba(56, 189, 248, 0.15)";
            }

            return (
              <div key={idx} style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "120px" }}>
                {/* Pointer indicator if pointing to this index */}
                <div style={{ height: "45px", display: "flex", gap: "6px", alignItems: "center" }}>
                  {pointers
                    .filter((p) => p.index === item.index)
                    .map((p, pIdx) => (
                      <div
                        key={pIdx}
                        style={{
                          backgroundColor: p.color || "#38bdf8",
                          color: "#0f172a",
                          padding: "3px 10px",
                          borderRadius: "8px",
                          fontSize: "16px",
                          fontWeight: 800,
                          transform: `translateY(${pulse}px)`,
                          boxShadow: `0 4px 12px ${p.color || "#38bdf8"}66`,
                        }}
                      >
                        {p.label} ↓
                      </div>
                    ))}
                </div>

                {/* Memory Cell Box */}
                <div
                  style={{
                    width: "100%",
                    height: "100px",
                    backgroundColor: bgColor,
                    border: `3px solid ${borderColor}`,
                    borderRadius: "16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "36px",
                    fontWeight: 800,
                    color: textColor,
                    boxShadow: isTarget ? "0 0 25px rgba(16, 185, 129, 0.5)" : "none",
                    transform: `scale(${progress})`,
                    transition: "all 0.2s ease",
                  }}
                >
                  {item.value}
                </div>

                {/* Index & Hex Address Label */}
                <div style={{ marginTop: "12px", textAlign: "center" }}>
                  <div style={{ fontSize: "16px", color: "#38bdf8", fontWeight: 700 }}>
                    Idx [{item.index}]
                  </div>
                  {item.address && (
                    <div style={{ fontSize: "12px", color: "#64748b", fontFamily: "monospace" }}>
                      {item.address}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend / Status Ribbon */}
        <div
          style={{
            display: "flex",
            gap: "28px",
            marginTop: "16px",
            padding: "10px 24px",
            backgroundColor: "rgba(30, 41, 59, 0.6)",
            borderRadius: "12px",
            border: "1px solid rgba(255, 255, 255, 0.08)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "16px", color: "#cbd5e1" }}>
            <span style={{ width: "12px", height: "12px", borderRadius: "3px", backgroundColor: "#38bdf8" }} />
            Active Sub-range
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "16px", color: "#cbd5e1" }}>
            <span style={{ width: "12px", height: "12px", borderRadius: "3px", backgroundColor: "#10b981" }} />
            Match / Target
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "16px", color: "#cbd5e1" }}>
            <span style={{ width: "12px", height: "12px", borderRadius: "3px", backgroundColor: "#64748b" }} />
            Pruned / Inactive
          </div>
        </div>
      </div>
    </div>
  );
};

// =========================================================================
// 1.5 QUEUE & FIFO DATA STRUCTURE VISUALIZER (For Queues, Ring Buffers, Deque)
// =========================================================================
export interface QueueItem {
  value: string | number;
  label?: string;
  status?: "front" | "rear" | "active" | "normal";
  index?: number;
}

export interface QueueVisualProps {
  visual_data?: {
    title?: string;
    items?: QueueItem[];
    stages?: any[];
    front_label?: string;
    rear_label?: string;
    direction_label?: string;
    status?: string;
    is_circular?: boolean;
  };
  text?: string;
}

export const QueueStructureVisual: React.FC<QueueVisualProps> = ({ visual_data, text }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const pulse = Math.sin(frame * 0.15) * 4;

  const title = visual_data?.title || text || "Queue Data Structure (FIFO)";

  // Parse items from either items array or stages array
  const rawItems = visual_data?.items && visual_data.items.length > 0
    ? visual_data.items
    : visual_data?.stages && visual_data.stages.length > 0
    ? visual_data.stages.map((s: any, i: number) => ({
        value: s.label?.replace(/^(Enqueue|Dequeue|Slot|\d+\.|\s*\[|\]|\s*\(.*?\))/gi, "").trim() || `Item ${i + 1}`,
        label: s.subtitle || s.badge || (i === 0 ? "Front" : i === visual_data.stages.length - 1 ? "Rear" : `Slot ${i}`),
        status: i === 0 ? "front" : i === visual_data.stages.length - 1 ? "rear" : "normal",
        index: i,
      }))
    : [
        { value: "Item [10]", label: "Front (Head)", status: "front", index: 0 },
        { value: "Item [20]", label: "Waiting", status: "normal", index: 1 },
        { value: "Item [30]", label: "Waiting", status: "normal", index: 2 },
        { value: "Item [40]", label: "Rear (Tail)", status: "rear", index: 3 },
      ];

  const items = rawItems;
  const frontIdx = 0;
  const rearIdx = items.length - 1;

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", color: "#f8fafc" }}>
      <h2 style={{ fontSize: "44px", fontWeight: 800, color: "#38bdf8", marginBottom: "25px", letterSpacing: "-0.5px" }}>
        {title}
      </h2>

      {/* Main Queue Stage Card */}
      <div
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.85)",
          border: "2px solid rgba(56, 189, 248, 0.3)",
          borderRadius: "24px",
          padding: "36px 45px",
          boxShadow: "0 30px 60px rgba(0, 0, 0, 0.7)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "20px",
          maxWidth: "1480px",
          width: "100%",
        }}
      >
        {/* Top Operational Direction Banner */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            width: "100%",
            maxWidth: "1150px",
            backgroundColor: "rgba(30, 41, 59, 0.6)",
            border: "1.5px solid rgba(56, 189, 248, 0.25)",
            borderRadius: "14px",
            padding: "10px 24px",
            fontSize: "18px",
            fontWeight: 700,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "#34d399" }}>
            <span style={{ fontSize: "22px" }}>📤</span>
            <span>DEQUEUE (Exit from Front)</span>
          </div>

          <div style={{ color: "#94a3b8", display: "flex", alignItems: "center", gap: "8px", fontSize: "16px" }}>
            <span>←</span>
            <span>Direction of FIFO Stream Flow</span>
            <span>←</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "#f59e0b" }}>
            <span>ENQUEUE (Enter at Rear)</span>
            <span style={{ fontSize: "22px" }}>📥</span>
          </div>
        </div>

        {/* Horizontal Queue Item Boxes */}
        <div style={{ display: "flex", gap: "18px", alignItems: "center", marginTop: "10px" }}>
          {items.map((item: any, idx: number) => {
            const isFront = idx === frontIdx || item.status === "front";
            const isRear = idx === rearIdx || item.status === "rear";

            let borderColor = "rgba(255, 255, 255, 0.15)";
            let bgColor = "rgba(30, 41, 59, 0.8)";
            let textColor = "#f8fafc";
            let pointerBadge = null;

            if (isFront) {
              borderColor = "#10b981";
              bgColor = "rgba(16, 185, 129, 0.22)";
              textColor = "#34d399";
              pointerBadge = (
                <div
                  style={{
                    backgroundColor: "#10b981",
                    color: "#0f172a",
                    padding: "4px 14px",
                    borderRadius: "8px",
                    fontSize: "15px",
                    fontWeight: 900,
                    transform: `translateY(${pulse}px)`,
                    boxShadow: "0 0 15px rgba(16, 185, 129, 0.7)",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  <span>Front Pointer</span>
                  <span>↓</span>
                </div>
              );
            } else if (isRear) {
              borderColor = "#f59e0b";
              bgColor = "rgba(245, 158, 11, 0.22)";
              textColor = "#fbbf24";
              pointerBadge = (
                <div
                  style={{
                    backgroundColor: "#f59e0b",
                    color: "#0f172a",
                    padding: "4px 14px",
                    borderRadius: "8px",
                    fontSize: "15px",
                    fontWeight: 900,
                    transform: `translateY(${pulse}px)`,
                    boxShadow: "0 0 15px rgba(245, 158, 11, 0.7)",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  <span>Rear Pointer</span>
                  <span>↓</span>
                </div>
              );
            }

            return (
              <React.Fragment key={idx}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "160px" }}>
                  {/* Top Pointer Badge Slot */}
                  <div style={{ height: "46px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    {pointerBadge}
                  </div>

                  {/* Queue Element Box */}
                  <div
                    style={{
                      width: "100%",
                      height: "110px",
                      backgroundColor: bgColor,
                      border: `3px solid ${borderColor}`,
                      borderRadius: "18px",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "26px",
                      fontWeight: 800,
                      color: textColor,
                      boxShadow: isFront
                        ? "0 0 30px rgba(16, 185, 129, 0.45)"
                        : isRear
                        ? "0 0 30px rgba(245, 158, 11, 0.45)"
                        : "0 10px 25px rgba(0, 0, 0, 0.4)",
                      transform: `scale(${progress})`,
                      transition: "all 0.2s ease",
                      gap: "4px",
                    }}
                  >
                    <span>{item.value}</span>
                  </div>

                  {/* Role Label & Index */}
                  <div style={{ marginTop: "10px", textAlign: "center" }}>
                    <div style={{ fontSize: "16px", color: isFront ? "#34d399" : isRear ? "#fbbf24" : "#94a3b8", fontWeight: 700 }}>
                      {item.label || `Slot [${idx}]`}
                    </div>
                    <div style={{ fontSize: "13px", color: "#64748b", fontFamily: "monospace" }}>
                      Index: {item.index !== undefined ? item.index : idx}
                    </div>
                  </div>
                </div>

                {/* Arrow between items pointing left towards Front */}
                {idx < items.length - 1 && (
                  <div style={{ fontSize: "28px", color: "rgba(56, 189, 248, 0.5)", marginTop: "40px", fontWeight: 900 }}>
                    ←
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Operational Invariant Footer */}
        <div
          style={{
            marginTop: "6px",
            backgroundColor: "rgba(16, 185, 129, 0.12)",
            border: "1.5px solid rgba(16, 185, 129, 0.35)",
            padding: "8px 28px",
            borderRadius: "999px",
            color: "#34d399",
            fontSize: "18px",
            fontWeight: 700,
          }}
        >
          {visual_data?.status || "FIFO Contract: First-In, First-Out • O(1) Enqueue (Rear) & O(1) Dequeue (Front)"}
        </div>
      </div>
    </div>
  );
};

// =========================================================================
// 2. TREE & HIERARCHY VISUALIZER (For Trees, Taxonomies, Decision Trees)
// =========================================================================
export interface TreeVisualProps {
  visual_data?: {
    title?: string;
    root_label?: string;
    left_label?: string;
    right_label?: string;
    left_leaf_1?: string;
    left_leaf_2?: string;
    right_leaf_1?: string;
    right_leaf_2?: string;
    status?: string;
  };
  text?: string;
}

export const TreeStructureVisual: React.FC<TreeVisualProps> = ({ visual_data, text }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });

  const title = visual_data?.title || text || "Hierarchical Tree Structure";

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", color: "#f8fafc" }}>
      <h2 style={{ fontSize: "44px", fontWeight: 800, color: "#38bdf8", marginBottom: "30px" }}>{title}</h2>

      <div
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.85)",
          border: "2px solid rgba(129, 140, 248, 0.3)",
          borderRadius: "24px",
          padding: "40px 60px",
          boxShadow: "0 30px 60px rgba(0, 0, 0, 0.7)",
          position: "relative",
          width: "1060px",
          height: "500px",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <svg width="960" height="420" viewBox="0 0 960 420" style={{ overflow: "visible" }}>
          {/* Branch Lines */}
          <line x1="480" y1="60" x2="240" y2="180" stroke="#818cf8" strokeWidth="4" opacity={progress} />
          <line x1="480" y1="60" x2="720" y2="180" stroke="#818cf8" strokeWidth="4" opacity={progress} />
          <line x1="240" y1="180" x2="120" y2="300" stroke="#64748b" strokeWidth="3" opacity={progress} />
          <line x1="240" y1="180" x2="360" y2="300" stroke="#34d399" strokeWidth="4" opacity={progress} />
          <line x1="720" y1="180" x2="600" y2="300" stroke="#64748b" strokeWidth="3" opacity={progress} />
          <line x1="720" y1="180" x2="840" y2="300" stroke="#64748b" strokeWidth="3" opacity={progress} />

          {/* Root Node */}
          <g transform={`translate(480, 60) scale(${progress})`}>
            <circle r="46" fill="#1e1b4b" stroke="#818cf8" strokeWidth="4" />
            <text textAnchor="middle" dy="8" fill="#ffffff" fontSize="22" fontWeight="700">
              {visual_data?.root_label || "Root: 50"}
            </text>
          </g>

          {/* Level 1 Nodes */}
          <g transform={`translate(240, 180) scale(${progress})`}>
            <circle r="42" fill="#1e293b" stroke="#38bdf8" strokeWidth="4" />
            <text textAnchor="middle" dy="8" fill="#38bdf8" fontSize="20" fontWeight="700">
              {visual_data?.left_label || "Left: 25"}
            </text>
          </g>

          <g transform={`translate(720, 180) scale(${progress})`}>
            <circle r="42" fill="#1e293b" stroke="#818cf8" strokeWidth="4" />
            <text textAnchor="middle" dy="8" fill="#818cf8" fontSize="20" fontWeight="700">
              {visual_data?.right_label || "Right: 75"}
            </text>
          </g>

          {/* Level 2 Leaves */}
          <g transform={`translate(120, 300) scale(${progress})`}>
            <rect x="-45" y="-25" width="90" height="50" rx="12" fill="#0f172a" stroke="#64748b" strokeWidth="2" />
            <text textAnchor="middle" dy="6" fill="#cbd5e1" fontSize="18" fontWeight="600">
              {visual_data?.left_leaf_1 || "12"}
            </text>
          </g>

          <g transform={`translate(360, 300) scale(${progress})`}>
            <rect x="-55" y="-28" width="110" height="56" rx="14" fill="#064e3b" stroke="#10b981" strokeWidth="3" />
            <text textAnchor="middle" dy="6" fill="#34d399" fontSize="20" fontWeight="800">
              {visual_data?.left_leaf_2 || "Target: 37"}
            </text>
          </g>

          <g transform={`translate(600, 300) scale(${progress})`}>
            <rect x="-45" y="-25" width="90" height="50" rx="12" fill="#0f172a" stroke="#64748b" strokeWidth="2" />
            <text textAnchor="middle" dy="6" fill="#cbd5e1" fontSize="18" fontWeight="600">
              {visual_data?.right_leaf_1 || "62"}
            </text>
          </g>

          <g transform={`translate(840, 300) scale(${progress})`}>
            <rect x="-45" y="-25" width="90" height="50" rx="12" fill="#0f172a" stroke="#64748b" strokeWidth="2" />
            <text textAnchor="middle" dy="6" fill="#cbd5e1" fontSize="18" fontWeight="600">
              {visual_data?.right_leaf_2 || "90"}
            </text>
          </g>
        </svg>

        {/* Dynamic Branch Decision Badge */}
        <div
          style={{
            position: "absolute",
            bottom: "20px",
            backgroundColor: "rgba(16, 185, 129, 0.15)",
            border: "1.5px solid #10b981",
            padding: "8px 24px",
            borderRadius: "999px",
            color: "#34d399",
            fontSize: "20px",
            fontWeight: 700,
          }}
        >
          {visual_data?.status || "Invariant: Left < Node < Right • Logarithmic O(log N) Traversal"}
        </div>
      </div>
    </div>
  );
};

// =========================================================================
// 3. UNIVERSAL DYNAMIC SYSTEM PIPELINE VISUALIZER (ANY Multi-Stage Process)
// =========================================================================
export interface PipelineStage {
  label: string;
  subtitle?: string;
  badge?: string;
  status?: "completed" | "active" | "highlight" | "normal";
  icon?: string;
  details?: string;
}

export interface SystemPipelineProps {
  visual_data?: {
    title?: string;
    stages?: PipelineStage[];
    highlight_label?: string;
  };
  text?: string;
}

export const SystemPipelineVisual: React.FC<SystemPipelineProps> = ({ visual_data, text }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const title = visual_data?.title || text || "End-to-End System Pipeline";

  const defaultStages: PipelineStage[] = [
    { label: "1. Ingestion", subtitle: "Raw Input Stream", badge: "Source", icon: "📥", status: "completed" },
    { label: "2. Processing", subtitle: "Transformation Engine", badge: "Engine", icon: "⚙️", status: "active" },
    { label: "3. Verification", subtitle: "Quality & Safety Check", badge: "Filter", icon: "🛡️", status: "normal" },
    { label: "4. Deployment", subtitle: "Delivered Output", badge: "Target", icon: "🚀", status: "highlight" },
  ];

  const stages = visual_data?.stages && visual_data.stages.length > 0 ? visual_data.stages : defaultStages;

  const stageCount = Math.max(stages.length, 1);
  const totalFrames = Math.max(1, durationInFrames);
  const stageFrames = totalFrames / stageCount;
  // Dynamic sequential transition across all stages paced to narration length
  const currentStageIndex = Math.min(stageCount - 1, Math.floor(frame / stageFrames));
  const stageProgress = ((frame % stageFrames) / stageFrames) || 0; // 0 to 1 within the current step
  const pulseAmount = Math.sin(stageProgress * Math.PI);

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", color: "#f8fafc" }}>
      <h2 style={{ fontSize: "44px", fontWeight: 800, color: "#38bdf8", marginBottom: "30px", letterSpacing: "-0.5px" }}>
        {title}
      </h2>

      <div
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.85)",
          border: "2px solid rgba(56, 189, 248, 0.3)",
          borderRadius: "24px",
          padding: "45px 50px",
          boxShadow: "0 30px 60px rgba(0, 0, 0, 0.7)",
          width: "100%",
          maxWidth: "1480px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          position: "relative",
        }}
      >
        {stages.map((stage, idx) => {
          const isCurrentActive = idx === currentStageIndex;
          const rawBadge = stage.badge?.trim();
          const stageBadge = rawBadge && !/^step\s*\d+$/i.test(rawBadge)
            ? rawBadge
            : `STEP ${idx + 1}`;

          const cardScale = isCurrentActive ? 1.03 + pulseAmount * 0.04 : 1.0;
          const cardBorder = isCurrentActive ? "#38bdf8" : "rgba(255, 255, 255, 0.12)";
          const cardBg = isCurrentActive ? "rgba(56, 189, 248, 0.2)" : "rgba(30, 41, 59, 0.7)";
          const cardShadow = isCurrentActive
            ? `0 0 ${25 + pulseAmount * 20}px rgba(56, 189, 248, 0.55)`
            : "none";

          return (
            <React.Fragment key={idx}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  padding: "26px 20px",
                  borderRadius: "20px",
                  backgroundColor: cardBg,
                  border: `2.5px solid ${cardBorder}`,
                  boxShadow: cardShadow,
                  transform: `scale(${cardScale}) translateY(${isCurrentActive ? -4 : 0}px)`,
                  transition: "all 0.2s ease",
                  flex: 1,
                  maxWidth: `${Math.floor(1200 / stages.length)}px`,
                  textAlign: "center",
                  position: "relative",
                }}
              >
                {/* Badge Tag */}
                <div
                  style={{
                    position: "absolute",
                    top: "-14px",
                    backgroundColor: isCurrentActive ? "#38bdf8" : "#475569",
                    color: isCurrentActive ? "#0f172a" : "#e2e8f0",
                    padding: "2px 14px",
                    borderRadius: "999px",
                    fontSize: "13px",
                    fontWeight: 800,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    boxShadow: isCurrentActive ? "0 0 12px rgba(56, 189, 248, 0.6)" : "none",
                  }}
                >
                  {stageBadge}
                </div>

                <div style={{ fontSize: "44px", marginBottom: "12px" }}>
                  {stage.icon || "⚡"}
                </div>

                <div style={{ fontSize: "22px", fontWeight: 800, color: "#ffffff", marginBottom: "6px" }}>
                  {stage.label}
                </div>

                {stage.subtitle && (
                  <div style={{ fontSize: "16px", color: isCurrentActive ? "#38bdf8" : "#94a3b8", lineHeight: 1.3 }}>
                    {stage.subtitle}
                  </div>
                )}

                {stage.details && (
                  <div style={{ marginTop: "10px", fontSize: "14px", color: "#64748b", fontFamily: "monospace" }}>
                    {stage.details}
                  </div>
                )}
              </div>

              {/* Connecting Pulse Connector */}
              {idx < stages.length - 1 && (() => {
                const isConnectorActive = currentStageIndex === idx;
                const beadProgress = isConnectorActive ? stageProgress : 0;
                return (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: "48px",
                      position: "relative",
                    }}
                  >
                    <div
                      style={{
                        width: "100%",
                        height: "4px",
                        backgroundColor: isConnectorActive ? "rgba(56, 189, 248, 0.7)" : "rgba(56, 189, 248, 0.2)",
                        position: "relative",
                        borderRadius: "2px",
                        boxShadow: isConnectorActive ? "0 0 10px rgba(56, 189, 248, 0.6)" : "none",
                      }}
                    >
                      {/* Moving pulse bead */}
                      {isConnectorActive && (
                        <div
                          style={{
                            position: "absolute",
                            top: "-4px",
                            left: `${beadProgress * 100}%`,
                            width: "12px",
                            height: "12px",
                            borderRadius: "50%",
                            backgroundColor: "#38bdf8",
                            boxShadow: "0 0 12px #38bdf8",
                          }}
                        />
                      )}
                    </div>
                  </div>
                );
              })()}
            </React.Fragment>
          );
        })}
      </div>

      <div
        style={{
          marginTop: "24px",
          backgroundColor: "rgba(30, 41, 59, 0.7)",
          borderRadius: "14px",
          padding: "12px 32px",
          fontSize: "20px",
          color: "#94a3b8",
          border: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        ✦ {visual_data?.highlight_label || "Seamless data transformation flow with strict boundary invariants."}
      </div>
    </div>
  );
};

// =========================================================================
// 4. UNIVERSAL CONCEPT NETWORK / MIND MAP VISUALIZER (ANY Interconnected System)
// =========================================================================
export interface NetworkNode {
  id?: string;
  label: string;
  desc?: string;
  badge?: string;
  color?: string;
  icon?: string;
}

export interface ConceptNetworkProps {
  visual_data?: {
    title?: string;
    core_concept?: {
      label: string;
      tag?: string;
      icon?: string;
    };
    nodes?: NetworkNode[];
  };
  text?: string;
}

export const ConceptNetworkVisual: React.FC<ConceptNetworkProps> = ({ visual_data, text }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const title = visual_data?.title || text || "Conceptual Knowledge Architecture";

  const coreLabel = visual_data?.core_concept?.label || visual_data?.core_concept?.name || visual_data?.central_hub || text || "Core Concept";
  const coreTag = visual_data?.core_concept?.tag || (visual_data?.central_hub ? "Central Graph Hub" : "Central Hub");
  const coreIcon = visual_data?.core_concept?.icon || (visual_data?.central_hub ? "🌐" : "💎");

  const defaultNodes: NetworkNode[] = [
    { label: "Principle A", desc: "Foundational Rule", badge: "Invariant", color: "#38bdf8", icon: "🧩" },
    { label: "Mechanics", desc: "Internal Operation", badge: "Engine", color: "#818cf8", icon: "⚙️" },
    { label: "Optimizations", desc: "Resource Scaling", badge: "Speed", color: "#10b981", icon: "⚡" },
    { label: "Real Application", desc: "Production Practice", badge: "Usage", color: "#f59e0b", icon: "🌐" },
  ];

  const rawNodes = visual_data?.nodes && visual_data.nodes.length > 0 ? visual_data.nodes : defaultNodes;
  const nodes = rawNodes.map((n: any, i: number) => ({
    label: n.label || n.title || n.name || `Node ${i + 1}`,
    desc: n.desc || n.description || n.role || "Interconnected architectural pillar.",
    badge: n.badge || n.tag || n.type || n.category || undefined,
    color: n.color || undefined,
    icon: n.icon || undefined,
  }));

  const totalFrames = Math.max(1, durationInFrames);
  const nodeDuration = totalFrames / Math.max(1, nodes.length);
  // Box glowing advances sequentially in sync with speech pacing: Box 1 -> Box 2 -> Box 3 -> Box 4
  const activeNodeIdx = Math.min(nodes.length - 1, Math.floor(frame / nodeDuration));
  const corePulse = Math.sin(frame * 0.1) * 3;

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", color: "#f8fafc" }}>
      <h2 style={{ fontSize: "44px", fontWeight: 800, color: "#38bdf8", marginBottom: "25px" }}>{title}</h2>

      <div
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.85)",
          border: "2px solid rgba(129, 140, 248, 0.3)",
          borderRadius: "24px",
          padding: "36px 40px",
          boxShadow: "0 30px 60px rgba(0, 0, 0, 0.7)",
          width: "100%",
          maxWidth: "1440px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "28px",
        }}
      >
        {/* Central Core Concept Node */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "18px",
            backgroundColor: "rgba(30, 27, 75, 0.9)",
            border: "3px solid #818cf8",
            borderRadius: "20px",
            padding: "16px 36px",
            boxShadow: `0 0 40px rgba(129, 140, 248, 0.5)`,
            transform: `scale(${1 + corePulse * 0.01})`,
          }}
        >
          <span style={{ fontSize: "36px" }}>{coreIcon}</span>
          <div>
            <div style={{ fontSize: "28px", fontWeight: 900, color: "#ffffff" }}>{coreLabel}</div>
            {coreTag && <div style={{ fontSize: "15px", color: "#c7d2fe", fontWeight: 600 }}>{coreTag}</div>}
          </div>
        </div>

        {/* Radiating Satellite Nodes Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(${Math.min(nodes.length, 4)}, 1fr)`,
            gap: "22px",
            width: "100%",
          }}
        >
          {nodes.map((node, idx) => {
            const isNodeActive = idx === activeNodeIdx;
            const nodeColor = node.color || ["#38bdf8", "#818cf8", "#10b981", "#f59e0b", "#ec4899"][idx % 5];
            return (
              <div
                key={idx}
                style={{
                  backgroundColor: isNodeActive ? "rgba(30, 41, 59, 0.95)" : "rgba(30, 41, 59, 0.75)",
                  border: `2px solid ${isNodeActive ? nodeColor : `${nodeColor}55`}`,
                  borderRadius: "18px",
                  padding: "24px 20px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  boxShadow: isNodeActive ? `0 0 25px ${nodeColor}66` : `0 10px 25px rgba(0, 0, 0, 0.5)`,
                  transform: isNodeActive ? "scale(1.04) translateY(-3px)" : "scale(1)",
                  transition: "all 0.2s ease",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                    <span style={{ fontSize: "32px" }}>{node.icon || "✦"}</span>
                    {node.badge && (
                      <span
                        style={{
                          backgroundColor: `${nodeColor}22`,
                          border: `1px solid ${nodeColor}`,
                          color: nodeColor,
                          fontSize: "13px",
                          fontWeight: 700,
                          padding: "3px 10px",
                          borderRadius: "999px",
                        }}
                      >
                        {node.badge}
                      </span>
                    )}
                  </div>
                  <h3 style={{ fontSize: "22px", fontWeight: 700, color: "#f8fafc", marginBottom: "8px" }}>
                    {node.label}
                  </h3>
                  <p style={{ fontSize: "16px", color: "#cbd5e1", lineHeight: 1.4, margin: 0 }}>
                    {node.desc || "Interconnected architectural pillar."}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// =========================================================================
// 5. UNIVERSAL LAYER STACK VISUALIZER (OSI, Memory, Tech Stacks, Deep Learning)
// =========================================================================
export interface StackLayer {
  title: string;
  description?: string;
  tag?: string;
  status?: "highlight" | "normal" | "accent";
  metrics?: string;
}

export interface LayerStackProps {
  visual_data?: {
    title?: string;
    layers?: StackLayer[];
    direction_label?: string;
  };
  text?: string;
}

export const LayerStackVisual: React.FC<LayerStackProps> = ({ visual_data, text }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const title = visual_data?.title || text || "Tiered Architectural Stack";

  const defaultLayers: StackLayer[] = [
    { title: "Application & Interface Tier", description: "User Interactions & API Endpoints", tag: "Layer 4", status: "normal" },
    { title: "Core Logic & Reasoning Engine", description: "Business Rules & Algorithmic State", tag: "Layer 3", status: "highlight" },
    { title: "Data Storage & Cache Layer", description: "Persistent Stores, Indexes & Relations", tag: "Layer 2", status: "normal" },
    { title: "Hardware & Compute Substrate", description: "CPU Registers, Memory & Network IO", tag: "Layer 1", status: "accent" },
  ];

  const layers = visual_data?.layers && visual_data.layers.length > 0 ? visual_data.layers : defaultLayers;

  const totalFrames = Math.max(1, durationInFrames);
  const layerDuration = totalFrames / Math.max(1, layers.length);
  // Layer highlight advances sequentially with narrator pacing
  const activeIndex = Math.min(layers.length - 1, Math.floor(frame / layerDuration));

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", color: "#f8fafc" }}>
      <h2 style={{ fontSize: "44px", fontWeight: 800, color: "#38bdf8", marginBottom: "25px" }}>{title}</h2>

      <div
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.85)",
          border: "2px solid rgba(56, 189, 248, 0.3)",
          borderRadius: "24px",
          padding: "36px 48px",
          boxShadow: "0 30px 60px rgba(0, 0, 0, 0.7)",
          width: "100%",
          maxWidth: "1350px",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
        }}
      >
        {layers.map((layer: any, idx) => {
          const isCurrent = idx === activeIndex;
          const isHighlight = isCurrent;

          const layerTitle = layer.title || layer.name || layer.layer || layer.label || `Layer ${layers.length - idx}`;
          const layerDesc = layer.description || layer.desc || layer.task || layer.role || layer.details || layer.function || "";
          const layerTag = layer.tag || layer.level || (layers.length === 7 ? `L${7 - idx}` : `L${layers.length - idx}`);
          const pdu = layer.pdu || (layerTag === "L7" || layerTag === "L6" || layerTag === "L5" ? "Data" : layerTag === "L4" ? "Segments" : layerTag === "L3" ? "Packets" : layerTag === "L2" ? "Frames" : layerTag === "L1" ? "Bits" : null);

          let borderColor = "rgba(255, 255, 255, 0.12)";
          let bgColor = "rgba(30, 41, 59, 0.7)";
          if (isHighlight) {
            borderColor = "#38bdf8";
            bgColor = "rgba(56, 189, 248, 0.18)";
          } else if (layer.status === "top" || layer.tag?.toUpperCase() === "TOP") {
            borderColor = "#10b981";
            bgColor = "rgba(16, 185, 129, 0.16)";
          } else if (layer.status === "accent") {
            borderColor = "#818cf8";
            bgColor = "rgba(129, 140, 248, 0.15)";
          }

          const roleLabel = layer.role_label !== undefined ? layer.role_label : (pdu ? "Role & Task:" : "");

          return (
            <div
              key={idx}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                backgroundColor: bgColor,
                border: `2.5px solid ${borderColor}`,
                borderRadius: "16px",
                padding: layers.length > 5 ? "14px 24px" : "18px 28px",
                boxShadow: isHighlight ? "0 0 30px rgba(56, 189, 248, 0.4)" : "none",
                transform: isHighlight ? "scale(1.02)" : "scale(1)",
                transition: "all 0.25s ease",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
                <div
                  style={{
                    backgroundColor: isHighlight ? "#38bdf8" : layer.status === "top" || layer.tag?.toUpperCase() === "TOP" ? "#10b981" : "rgba(255, 255, 255, 0.1)",
                    color: isHighlight || layer.status === "top" || layer.tag?.toUpperCase() === "TOP" ? "#0f172a" : "#cbd5e1",
                    padding: "4px 12px",
                    borderRadius: "8px",
                    fontSize: "15px",
                    fontWeight: 800,
                  }}
                >
                  {layerTag}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
                  <div style={{ fontSize: layers.length > 5 ? "20px" : "23px", fontWeight: 800, color: "#ffffff", letterSpacing: "-0.3px", display: "flex", alignItems: "center", gap: "10px" }}>
                    <span>{layerTitle}</span>
                    {layer.pointer && (
                      <span style={{ fontSize: "12px", padding: "2px 8px", borderRadius: "6px", backgroundColor: "#f59e0b", color: "#0f172a", fontWeight: 900 }}>
                        {layer.pointer}
                      </span>
                    )}
                    {pdu && (
                      <span style={{ fontSize: "11px", padding: "2px 8px", borderRadius: "6px", backgroundColor: "rgba(56, 189, 248, 0.2)", color: "#7dd3fc", fontWeight: 700 }}>
                        PDU: {pdu}
                      </span>
                    )}
                  </div>
                  {layerDesc && (
                    <div style={{ fontSize: layers.length > 5 ? "15px" : "17px", color: isHighlight ? "#7dd3fc" : "#cbd5e1", lineHeight: 1.35 }}>
                      {roleLabel ? <span style={{ color: "#38bdf8", fontWeight: 700, marginRight: "6px" }}>{roleLabel}</span> : null}
                      {layerDesc}
                    </div>
                  )}
                </div>
              </div>

              {(layer.metrics || layer.protocol) && (
                <div style={{ fontSize: "14px", color: "#34d399", fontFamily: "monospace", fontWeight: 700, backgroundColor: "rgba(16, 185, 129, 0.12)", padding: "4px 12px", borderRadius: "8px" }}>
                  {layer.metrics || layer.protocol}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: "20px", fontSize: "18px", color: "#64748b" }}>
        ↕ {visual_data?.direction_label || "Bidirectional Communication: Abstraction boundary between higher & lower tiers"}
      </div>
    </div>
  );
};

// =========================================================================
// 6. UNIVERSAL CYCLE LOOP VISUALIZER (Event Loop, CPU Cycle, Life Cycles)
// =========================================================================
export interface CycleStage {
  title: string;
  desc?: string;
  icon?: string;
}

export interface CycleLoopProps {
  visual_data?: {
    title?: string;
    stages?: CycleStage[];
    center_label?: string;
  };
  text?: string;
}

export const CycleLoopVisual: React.FC<CycleLoopProps> = ({ visual_data, text }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const title = visual_data?.title || text || "Continuous Execution Cycle";

  const defaultStages: CycleStage[] = [
    { title: "Fetch / Input", desc: "Retrieve next instruction or token", icon: "📥" },
    { title: "Evaluate / Decode", desc: "Parse syntactic structure and intent", icon: "🧠" },
    { title: "Execute Action", desc: "Perform operation on environment", icon: "⚡" },
    { title: "Store / Feedback", desc: "Record state transition & loop", icon: "💾" },
  ];

  const stages = visual_data?.stages && visual_data.stages.length > 0 ? visual_data.stages : defaultStages;

  const totalFrames = Math.max(1, durationInFrames);
  const stageDuration = totalFrames / Math.max(1, stages.length);
  // Active stage rotates sequentially with narration pacing
  const activeIndex = Math.min(stages.length - 1, Math.floor(frame / stageDuration));

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", color: "#f8fafc" }}>
      <h2 style={{ fontSize: "44px", fontWeight: 800, color: "#38bdf8", marginBottom: "30px" }}>{title}</h2>

      <div
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.85)",
          border: "2px solid rgba(56, 189, 248, 0.3)",
          borderRadius: "24px",
          padding: "50px 60px",
          boxShadow: "0 30px 60px rgba(0, 0, 0, 0.7)",
          width: "100%",
          maxWidth: "1350px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        {stages.map((stage, idx) => {
          const isActive = idx === activeIndex;
          return (
            <React.Fragment key={idx}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  padding: "26px 20px",
                  borderRadius: "20px",
                  backgroundColor: isActive ? "rgba(56, 189, 248, 0.2)" : "rgba(30, 41, 59, 0.7)",
                  border: `3px solid ${isActive ? "#38bdf8" : "rgba(255, 255, 255, 0.1)"}`,
                  boxShadow: isActive ? `0 0 35px rgba(56, 189, 248, 0.5)` : "none",
                  transform: isActive ? "scale(1.08)" : "scale(1)",
                  transition: "all 0.25s ease",
                  width: `${Math.floor(1000 / stages.length)}px`,
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: "44px", marginBottom: "12px" }}>{stage.icon || "🔄"}</div>
                <div style={{ fontSize: "20px", fontWeight: 800, color: isActive ? "#ffffff" : "#cbd5e1" }}>
                  {stage.title}
                </div>
                {stage.desc && (
                  <div style={{ fontSize: "14px", color: isActive ? "#38bdf8" : "#94a3b8", marginTop: "6px" }}>
                    {stage.desc}
                  </div>
                )}
              </div>

              {idx < stages.length - 1 && (
                <div style={{ fontSize: "34px", color: isActive ? "#38bdf8" : "#475569" }}>➔</div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      <div
        style={{
          marginTop: "24px",
          backgroundColor: "rgba(30, 41, 59, 0.7)",
          borderRadius: "14px",
          padding: "12px 30px",
          fontSize: "20px",
          color: "#94a3b8",
          border: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        🔄 {visual_data?.center_label || "Continuous invariant loop: Output of each phase forms the precondition for the next."}
      </div>
    </div>
  );
};

// =========================================================================
// 7. UNIVERSAL COMPARISON MATRIX (Trade-Offs, SQL vs NoSQL, Paradigms)
// =========================================================================
export interface ComparisonRow {
  feature: string;
  left_val: string;
  right_val: string;
  winner?: "left" | "right" | "tie";
}

export interface ComparisonMatrixProps {
  visual_data?: {
    title?: string;
    left_title?: string;
    right_title?: string;
    rows?: ComparisonRow[];
  };
  text?: string;
}

export const ComparisonMatrixVisual: React.FC<ComparisonMatrixProps> = ({ visual_data, text }) => {
  const title = visual_data?.title || text || "Comparative Architectural Trade-Offs";
  const titleLower = `${title} ${text || ""}`.toLowerCase();

  const isNetwork = ["tcp", "ip", "osi", "layer", "protocol", "network", "packet", "segment", "window", "flow", "header"].some(k => titleLower.includes(k));
  const isAlgo = ["tree", "array", "search", "sort", "recursion", "graph", "binary"].some(k => titleLower.includes(k));

  let defaultRows: ComparisonRow[];
  let defaultLeftTitle = "Traditional / Naive";
  let defaultRightTitle = "Optimized Architecture";

  if (isNetwork) {
    defaultLeftTitle = "Stop-and-Wait / Unchecked";
    defaultRightTitle = "Pipelined Sliding Window";
    defaultRows = [
      { feature: "Transmission Mode", left_val: "Stop-and-Wait (1 Pkt / RTT)", right_val: "Continuous Pipelining (rwnd)", winner: "right" },
      { feature: "Header Protocol State", left_val: "Unframed Monolithic Bytes", right_val: "Deterministic Seq & ACK Numbers", winner: "right" },
      { feature: "Buffer Safety", left_val: "Kernel Buffer Exhaustion", right_val: "Dynamic Advertised Window (rwnd)", winner: "right" },
      { feature: "Loss Recovery", left_val: "RTO Timeout Idle Stalls", right_val: "Fast Retransmit & 3x Dup ACKs", winner: "right" },
    ];
  } else if (isAlgo) {
    defaultLeftTitle = "Naive Linear Scan";
    defaultRightTitle = "Logarithmic Structure";
    defaultRows = [
      { feature: "Time Complexity", left_val: "O(N) Linear Time", right_val: "O(log N) Logarithmic", winner: "right" },
      { feature: "Memory Overhead", left_val: "O(1) In-Place", right_val: "O(log N) Auxiliary Stack", winner: "left" },
      { feature: "Implementation", left_val: "Simple Linear Traversal", right_val: "Balanced Tree Invariant", winner: "tie" },
      { feature: "Large N Scaling", left_val: "Bottlenecks on Big Data", right_val: "High-Throughput Sub-Millisecond", winner: "right" },
    ];
  } else {
    defaultLeftTitle = "Tightly Coupled Monolith";
    defaultRightTitle = "Modular Decoupled Tiers";
    defaultRows = [
      { feature: "Modularity & Scope", left_val: "Monolithic Coupling", right_val: "Strict Layer Abstraction", winner: "right" },
      { feature: "Fault Tolerance", left_val: "Cascading Component Failure", right_val: "Isolated Tier Resilience", winner: "right" },
      { feature: "State Invariants", left_val: "Leaking Global Side Effects", right_val: "Deterministic State Machine", winner: "right" },
      { feature: "System Scalability", left_val: "Single Node Lock Contention", right_val: "Horizontal Independent Scale", winner: "right" },
    ];
  }

  const leftTitle = visual_data?.left_title || (visual_data as any)?.leftHeader || defaultLeftTitle;
  const rightTitle = visual_data?.right_title || (visual_data as any)?.rightHeader || defaultRightTitle;
  const rawRows = visual_data?.rows && visual_data.rows.length > 0 ? visual_data.rows : defaultRows;

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", color: "#f8fafc" }}>
      <h2 style={{ fontSize: "44px", fontWeight: 800, color: "#38bdf8", marginBottom: "25px" }}>{title}</h2>

      <div
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.85)",
          border: "2px solid rgba(56, 189, 248, 0.3)",
          borderRadius: "24px",
          padding: "36px 44px",
          boxShadow: "0 30px 60px rgba(0, 0, 0, 0.7)",
          width: "100%",
          maxWidth: "1350px",
        }}
      >
        {/* Table Header */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.2fr 1.5fr 1.5fr",
            padding: "16px 24px",
            borderBottom: "2px solid rgba(255, 255, 255, 0.12)",
            fontSize: "22px",
            fontWeight: 800,
          }}
        >
          <div style={{ color: "#94a3b8" }}>Evaluated Dimension</div>
          <div style={{ color: "#38bdf8", display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#38bdf8" }} />
            {leftTitle}
          </div>
          <div style={{ color: "#a78bfa", display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#a78bfa" }} />
            {rightTitle}
          </div>
        </div>

        {/* Rows */}
        {rawRows.map((row: any, idx) => {
          const fallback = defaultRows[idx % defaultRows.length];
          const featureName = row.feature || row.dimension || row.aspect || row.name || fallback.feature;
          const leftText = row.left_val || row.left || row.left_value || row.traditional || row.naive || fallback.left_val;
          const rightText = row.right_val || row.right || row.right_value || row.optimized || row.modern || fallback.right_val;
          const winner = row.winner;

          let leftColor = "#e2e8f0";
          let rightColor = "#e2e8f0";
          if (winner === "left") {
            leftColor = "#34d399";
          } else if (winner === "right") {
            rightColor = "#34d399";
          }

          return (
            <div
              key={idx}
              style={{
                display: "grid",
                gridTemplateColumns: "1.2fr 1.5fr 1.5fr",
                padding: "18px 24px",
                borderBottom: idx < rawRows.length - 1 ? "1px solid rgba(255, 255, 255, 0.06)" : "none",
                backgroundColor: idx % 2 === 0 ? "rgba(30, 41, 59, 0.45)" : "transparent",
                borderRadius: "10px",
                alignItems: "center",
                fontSize: "20px",
              }}
            >
              <div style={{ fontWeight: 700, color: "#f8fafc" }}>{featureName}</div>
              <div style={{ color: leftColor, fontWeight: winner === "left" ? 700 : 400, lineHeight: 1.4 }}>
                {leftText}
              </div>
              <div style={{ color: rightColor, fontWeight: winner === "right" ? 700 : 400, lineHeight: 1.4 }}>
                {rightText}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// =========================================================================
// 8. PRESERVED LEGACY PRESETS (Backward Compatibility)
// =========================================================================
export interface GenAIVisualProps {
  visual_data?: Record<string, unknown>;
  text?: string;
}

export const GenAITransformerVisual: React.FC<GenAIVisualProps> = ({ visual_data, text }) => {
  return (
    <SystemPipelineVisual
      visual_data={{
        title: (visual_data?.title as string) || text || "Transformer Attention & Next-Token Generation",
        stages: [
          { label: "1. Prompt Input", subtitle: "Text Tokens", badge: "Tokens", icon: "🔤", status: "completed" },
          { label: "2. Vector Embeddings", subtitle: "High-Dim Latent Space", badge: "Vectors", icon: "📐", status: "completed" },
          { label: "3. Multi-Head Attention", subtitle: "Context Correlation", badge: "Attention", icon: "🧠", status: "active" },
          { label: "4. Softmax Projection", subtitle: "Token Probabilities", badge: "Output", icon: "🎯", status: "highlight" },
        ],
        highlight_label: "Transformer self-attention calculates deep token relationships across entire sequences.",
      }}
    />
  );
};

export interface AgenticLoopVisualProps {
  visual_data?: Record<string, unknown>;
  text?: string;
}

export const AgenticLoopVisual: React.FC<AgenticLoopVisualProps> = ({ visual_data, text }) => {
  return (
    <CycleLoopVisual
      visual_data={{
        title: (visual_data?.title as string) || text || "Agentic AI: Autonomous Reasoning Loop",
        stages: [
          { title: "1. Goal Input", desc: "User prompt & constraints", icon: "🎯" },
          { title: "2. Reasoning & Plan", desc: "Chain-of-thought breakdown", icon: "🧠" },
          { title: "3. Tool Execution", desc: "APIs, search, and code run", icon: "🛠️" },
          { title: "4. Reflect & Verify", desc: "State check & completion gate", icon: "🔍" },
        ],
        center_label: "ReAct Loop: Agent repeatedly acts, observes feedback, and self-refines until objective is satisfied.",
      }}
    />
  );
};
