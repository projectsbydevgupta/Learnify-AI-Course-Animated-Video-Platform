import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { GraphChart } from "./GraphChart";
import {
  ArrayMemoryVisual,
  TreeStructureVisual,
  GenAITransformerVisual,
  AgenticLoopVisual,
  SystemPipelineVisual,
  ConceptNetworkVisual,
  LayerStackVisual,
  CycleLoopVisual,
  ComparisonMatrixVisual,
  QueueStructureVisual
} from "./VisualLibrary";

export interface VisualDataPayload {
  title?: string;
  subtitle?: string;
  description?: string;
  code?: string;
  steps?: Array<{ title?: string; desc?: string } | string>;
  stages?: any[]; // eslint-disable-line @typescript-eslint/no-explicit-any
  nodes?: any[]; // eslint-disable-line @typescript-eslint/no-explicit-any
  layers?: any[]; // eslint-disable-line @typescript-eslint/no-explicit-any
  items?: any[]; // eslint-disable-line @typescript-eslint/no-explicit-any
  pointers?: any[]; // eslint-disable-line @typescript-eslint/no-explicit-any
  rows?: any[]; // eslint-disable-line @typescript-eslint/no-explicit-any
  left_title?: string;
  left_desc?: string;
  right_title?: string;
  right_desc?: string;
  [key: string]: unknown;
}

export interface SceneData {
  scene_id: number;
  start_time: number;
  end_time: number;
  narration: string;
  visual_type: string;
  visual_data: VisualDataPayload;
  text: string;
  transition: string;
}

export const SceneRenderer: React.FC<{ scene: SceneData }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scene duration in frames dynamically aligned to composition FPS
  const sceneDurationFrames = Math.max(fps, Math.round(((scene.end_time || 5) - (scene.start_time || 0)) * fps));
  const exitFramesCount = Math.round(fps * 0.45);
  const exitStart = Math.max(12, sceneDurationFrames - exitFramesCount);

  // Entrance and exit motion interpolation
  const enterOpacity = interpolate(frame, [0, 14], [0, 1], {
    extrapolateRight: "clamp",
  });
  const exitOpacity = interpolate(frame, [exitStart, sceneDurationFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = Math.min(enterOpacity, exitOpacity);

  const transitionType = (scene.transition || "slide_up").toLowerCase();

  let enterTranslateY = 0;
  let exitTranslateY = 0;
  let enterTranslateX = 0;
  let exitTranslateX = 0;
  let enterScale = 1;
  let exitScale = 1;

  if (transitionType.includes("slide_up") || transitionType === "slide") {
    enterTranslateY = interpolate(frame, [0, 16], [35, 0], { extrapolateRight: "clamp" });
    exitTranslateY = interpolate(frame, [exitStart, sceneDurationFrames], [0, -30], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (transitionType.includes("zoom") || transitionType.includes("scale")) {
    enterScale = interpolate(frame, [0, 18], [0.94, 1], { extrapolateRight: "clamp" });
    exitScale = interpolate(frame, [exitStart, sceneDurationFrames], [1, 1.05], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else {
    // Default smooth motion
    enterTranslateY = interpolate(frame, [0, 16], [30, 0], { extrapolateRight: "clamp" });
    exitTranslateY = interpolate(frame, [exitStart, sceneDurationFrames], [0, -20], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    enterScale = interpolate(frame, [0, 18], [0.97, 1], { extrapolateRight: "clamp" });
  }

  const translateY = enterTranslateY + exitTranslateY;
  const translateX = enterTranslateX + exitTranslateX;
  const scale = enterScale * exitScale;

  // Modern cosmic background with radial glows (Optimized for maximum rendering speed)
  const bgStyle: React.CSSProperties = {
    background: "radial-gradient(ellipse at 50% 20%, #1e1b4b 0%, #090d1e 60%, #030712 100%)",
    color: "#f8fafc",
    fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "45px 80px 25px 80px",
    position: "relative",
    overflow: "hidden",
  };

  // Ambient background blur orbs (Static for instant Chromium rasterization)
  const orb1Style: React.CSSProperties = {
    position: "absolute",
    top: "-150px",
    right: "-100px",
    width: "600px",
    height: "600px",
    borderRadius: "50%",
    background: "rgba(56, 189, 248, 0.12)",
    filter: "blur(140px)",
    pointerEvents: "none",
  };

  const orb2Style: React.CSSProperties = {
    position: "absolute",
    bottom: "-150px",
    left: "-100px",
    width: "600px",
    height: "600px",
    borderRadius: "50%",
    background: "rgba(129, 140, 248, 0.12)",
    filter: "blur(140px)",
    pointerEvents: "none",
  };

  // Glassmorphic main stage card
  const mainStageStyle: React.CSSProperties = {
    backgroundColor: "rgba(15, 23, 42, 0.7)",
    backdropFilter: "blur(20px)",
    borderRadius: "28px",
    border: "1px solid rgba(255, 255, 255, 0.1)",
    padding: "40px 60px",
    width: "100%",
    maxWidth: "1640px",
    height: "630px",
    boxShadow: "0 25px 60px -15px rgba(0, 0, 0, 0.7), inset 0 1px 0 0 rgba(255, 255, 255, 0.1)",
    opacity,
    transform: `translateY(${translateY}px) translateX(${translateX}px) scale(${scale})`,
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
  };

  // Subtitle banner elevated in the lower third so it is never covered by video player controls
  const subtitleBarStyle: React.CSSProperties = {
    width: "100%",
    maxWidth: "1540px",
    backgroundColor: "rgba(7, 12, 26, 0.94)",
    backdropFilter: "blur(24px)",
    border: "1.5px solid rgba(56, 189, 248, 0.4)",
    borderRadius: "22px",
    padding: "16px 36px",
    display: "flex",
    alignItems: "center",
    gap: "20px",
    boxShadow: "0 15px 35px rgba(0, 0, 0, 0.8), 0 0 20px rgba(56, 189, 248, 0.15)",
    opacity,
    transform: `translateY(${translateY * 0.5}px)`,
    marginBottom: "50px",
    zIndex: 30,
  };

  return (
    <AbsoluteFill style={bgStyle}>
      <div style={orb1Style} />
      <div style={orb2Style} />

      {/* Top Header Bar */}
      <div
        style={{
          width: "100%",
          maxWidth: "1640px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          opacity,
          padding: "0 10px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div
            style={{
              width: "14px",
              height: "14px",
              borderRadius: "50%",
              backgroundColor: "#38bdf8",
              boxShadow: "0 0 12px #38bdf8",
            }}
          />
          <span style={{ fontSize: "22px", fontWeight: 700, color: "#cbd5e1", letterSpacing: "1px", textTransform: "uppercase" }}>
            Interactive Video Lecture
          </span>
        </div>

        <div
          style={{
            backgroundColor: "rgba(30, 41, 59, 0.8)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            padding: "8px 22px",
            borderRadius: "999px",
            fontSize: "20px",
            fontWeight: 600,
            color: "#38bdf8",
          }}
        >
          Scene {scene.scene_id} • {scene.text || "Core Concept"}
        </div>
      </div>

      {/* Center Stage Presentation */}
      <div style={mainStageStyle}>
        {/* Visual Type 1: Clean, High-Speed Remotion Title Card */}
        {scene.visual_type === "title_card" && (
          <div style={{ textAlign: "center", maxWidth: "1280px" }}>
            <div
              style={{
                display: "inline-block",
                padding: "8px 24px",
                borderRadius: "999px",
                backgroundColor: "rgba(56, 189, 248, 0.15)",
                border: "1px solid rgba(56, 189, 248, 0.35)",
                color: "#38bdf8",
                fontSize: "26px",
                fontWeight: 700,
                marginBottom: "28px",
                letterSpacing: "1.5px",
                textTransform: "uppercase",
              }}
            >
              🚀 Foundation & Overview
            </div>

            <h1
              style={{
                fontSize: "82px",
                fontWeight: 900,
                lineHeight: 1.15,
                background: "linear-gradient(135deg, #ffffff 0%, #38bdf8 50%, #818cf8 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                marginBottom: "30px",
                letterSpacing: "-1px",
              }}
            >
              {scene.visual_data.title || scene.text}
            </h1>

            <p
              style={{
                fontSize: "36px",
                color: "#94a3b8",
                fontWeight: 400,
                maxWidth: "960px",
                margin: "0 auto",
                lineHeight: 1.5,
              }}
            >
              {scene.visual_data.subtitle || "A clear, intuitive guide designed for mastery."}
            </p>
          </div>
        )}

        {/* Visual Type 2: Graph / Interactive Diagram */}
        {scene.visual_type === "graph_chart" && (
          <GraphChart visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Visual Type: Array Memory Structure (For Arrays, Two Pointers, Binary Search) */}
        {scene.visual_type === "array_memory" && (
          <ArrayMemoryVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Visual Type: Queue & FIFO Structure (For Queues, Circular Buffers, Deques) */}
        {(scene.visual_type === "queue_structure" || scene.visual_type === "queue_pipeline" || scene.visual_type === "fifo_queue") && (
          <QueueStructureVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Visual Type: Tree Hierarchy (For Decision Trees, BST, Heaps) */}
        {scene.visual_type === "tree_structure" && (
          <TreeStructureVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Visual Type: Generative AI & Transformers (For LLMs, Attention, Tokens) */}
        {scene.visual_type === "genai_transformer" && (
          <GenAITransformerVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Visual Type: Agentic AI Loop (For Autonomous Agents, ReAct, Workflows) */}
        {scene.visual_type === "agentic_loop" && (
          <AgenticLoopVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Dynamic Visual 1: Universal System Pipeline (ANY workflow, protocol, stages) */}
        {(scene.visual_type === "system_pipeline" || scene.visual_type === "pipeline") && (
          <SystemPipelineVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Dynamic Visual 2: Universal Concept Knowledge Network (ANY mind map / principles) */}
        {(scene.visual_type === "concept_network" || scene.visual_type === "concept_map") && (
          <ConceptNetworkVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Dynamic Visual 3: Universal Layer Stack (ANY tiered architecture / stacks) */}
        {(scene.visual_type === "layer_stack" || scene.visual_type === "stack_hierarchy") && (
          <LayerStackVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Dynamic Visual 4: Universal Cycle Loop (ANY recurring cycle or execution loop) */}
        {(scene.visual_type === "cycle_loop" || scene.visual_type === "circular_cycle") && (
          <CycleLoopVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Dynamic Visual 5: Universal Comparison Matrix (ANY trade-offs / feature grid) */}
        {(scene.visual_type === "comparison_matrix" || scene.visual_type === "data_grid") && (
          <ComparisonMatrixVisual visual_data={scene.visual_data} text={scene.text} />
        )}

        {/* Visual Type 3: Step-by-Step Flow Cards */}
        {scene.visual_type === "flow_steps" && (
          <div style={{ width: "100%", maxWidth: "1400px" }}>
            <h2
              style={{
                fontSize: "48px",
                fontWeight: 800,
                color: "#38bdf8",
                textAlign: "center",
                marginBottom: "48px",
              }}
            >
              {scene.text}
            </h2>

            {(() => {
              const steps = Array.isArray(scene.visual_data.steps) ? scene.visual_data.steps : [];
              const stepCount = Math.max(steps.length, 1);
              const stepDuration = Math.max(1, sceneDurationFrames) / stepCount;
              // Glowing effect advances calmly to next step as narrator proceeds
              const activeStepIdx = steps.length > 0
                ? Math.min(steps.length - 1, Math.floor(frame / stepDuration))
                : 0;
              const colCount = Math.min(Math.max(steps.length, 1), 4);

              return (
                <div style={{ display: "grid", gridTemplateColumns: `repeat(${colCount}, 1fr)`, gap: "28px" }}>
                  {steps.map((step, idx: number) => {
                    const stepTitle = typeof step === "object" && step !== null && "title" in step ? step.title : `Stage ${idx + 1}`;
                    const stepDesc = typeof step === "object" && step !== null && "desc" in step ? step.desc : String(step);
                    const isStepActive = idx === activeStepIdx;

                    return (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: isStepActive ? "rgba(56, 189, 248, 0.18)" : "rgba(30, 41, 59, 0.8)",
                          border: `2px solid ${isStepActive ? "#38bdf8" : "rgba(255, 255, 255, 0.12)"}`,
                          borderRadius: "20px",
                          padding: "36px 30px",
                          boxShadow: isStepActive ? "0 0 35px rgba(56, 189, 248, 0.45)" : "0 15px 35px rgba(0, 0, 0, 0.4)",
                          transform: isStepActive ? "scale(1.04) translateY(-4px)" : "scale(1)",
                          transition: "all 0.2s ease",
                          display: "flex",
                          flexDirection: "column",
                          justifyContent: "space-between",
                        }}
                      >
                        <div>
                          <div
                            style={{
                              width: "56px",
                              height: "56px",
                              borderRadius: "16px",
                              backgroundColor: isStepActive ? "#38bdf8" : "#475569",
                              color: isStepActive ? "#0f172a" : "#e2e8f0",
                              fontSize: "28px",
                              fontWeight: 900,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              marginBottom: "20px",
                              boxShadow: isStepActive ? "0 0 16px rgba(56, 189, 248, 0.6)" : "none",
                            }}
                          >
                            {idx + 1}
                          </div>
                          <h3 style={{ fontSize: "28px", fontWeight: 700, color: "#f8fafc", marginBottom: "14px" }}>
                            {stepTitle}
                          </h3>
                          <p style={{ fontSize: "22px", color: isStepActive ? "#e2e8f0" : "#cbd5e1", lineHeight: 1.5 }}>
                            {stepDesc}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })()}
          </div>
        )}

        {/* Visual Type 4: Side-by-Side Comparison */}
        {scene.visual_type === "comparison" && (
          <div style={{ width: "100%", maxWidth: "1350px" }}>
            <h2
              style={{
                fontSize: "48px",
                fontWeight: 800,
                color: "#38bdf8",
                textAlign: "center",
                marginBottom: "40px",
              }}
            >
              {scene.text}
            </h2>

            {(() => {
              const textLower = `${scene.text || ""} ${scene.narration || ""}`.toLowerCase();
              const isML = ["forest", "decision tree", "regression", "machine learning", "neural", "gradient", "model", "overfitting", "underfitting", "bias", "variance", "loss", "gini"].some(k => textLower.includes(k));
              const isDBMS = ["normalization", "normal form", "1nf", "2nf", "3nf", "bcnf", "acid", "transaction", "database", "sql", "anomaly", "serializable", "locking"].some(k => textLower.includes(k));
              const isDSA = ["array", "pointer", "binary search", "search", "sort", "quicksort", "lomuto", "partition", "recursion", "stack", "graph", "pivot"].some(k => textLower.includes(k));
              const isNetwork = ["tcp", "ip", "osi", "layer", "protocol", "network", "window", "flow", "header", "packet", "handshake"].some(k => textLower.includes(k));

              let defLeftTitle = "Traditional / Monolith";
              let defLeftDesc = "Tightly coupled components where one layer error cascades into total system failure.";
              let defRightTitle = "Modular Architecture";
              let defRightDesc = "Strict abstraction boundaries where each tier operates independently and reliably.";

              if (isML) {
                defLeftTitle = "Single Tree / High Variance";
                defLeftDesc = "Overfits to training noise, leading to high prediction variance and poor out-of-bag generalization.";
                defRightTitle = "Ensemble / Controlled Variance";
                defRightDesc = "Averages decorrelated predictions across bootstrapped subsets with feature subsampling.";
              } else if (isDBMS) {
                defLeftTitle = "Unnormalized / Redundant Schema";
                defLeftDesc = "Repeated data attributes leading to insertion, update, and deletion anomalies or lock contention.";
                defRightTitle = "Normalized BCNF / Serializability";
                defRightDesc = "Decomposed lossless relations enforcing functional integrity and ACID guarantees.";
              } else if (isDSA) {
                defLeftTitle = "Naive Brute Force (O(N) / O(N²))";
                defLeftDesc = "Unchecked linear scan examining every single element with redundant comparisons.";
                defRightTitle = "Divide & Conquer (O(log N))";
                defRightDesc = "Deterministically halving the search space or partition boundaries with invariant bounds.";
              } else if (isNetwork) {
                defLeftTitle = "Stop-and-Wait / Unchecked";
                defLeftDesc = "Sender pauses after every single packet, starving line bandwidth and risking buffer drops.";
                defRightTitle = "Sliding-Window Flow Control";
                defRightDesc = "Continuous streaming dynamically bounded by receiver advertised window (rwnd).";
              }

              const leftTitle = scene.visual_data.left_title || defLeftTitle;
              const leftDesc = scene.visual_data.left_desc || defLeftDesc;
              const rightTitle = scene.visual_data.right_title || defRightTitle;
              const rightDesc = scene.visual_data.right_desc || defRightDesc;

              return (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "36px" }}>
                  {/* Left: Approach / Paradigm A */}
                  <div
                    style={{
                      backgroundColor: "rgba(15, 23, 42, 0.85)",
                      border: "2px solid rgba(56, 189, 248, 0.35)",
                      borderRadius: "22px",
                      padding: "40px",
                      boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5)",
                    }}
                  >
                    <div style={{ fontSize: "30px", fontWeight: 800, color: "#38bdf8", marginBottom: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
                      <span style={{ width: "12px", height: "12px", borderRadius: "50%", backgroundColor: "#38bdf8", boxShadow: "0 0 10px #38bdf8" }} />
                      {leftTitle}
                    </div>
                    <p style={{ fontSize: "24px", color: "#e2e8f0", lineHeight: 1.6 }}>
                      {leftDesc}
                    </p>
                  </div>

                  {/* Right: Approach / Paradigm B */}
                  <div
                    style={{
                      backgroundColor: "rgba(15, 23, 42, 0.85)",
                      border: "2px solid rgba(167, 139, 250, 0.35)",
                      borderRadius: "22px",
                      padding: "40px",
                      boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5)",
                    }}
                  >
                    <div style={{ fontSize: "30px", fontWeight: 800, color: "#a78bfa", marginBottom: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
                      <span style={{ width: "12px", height: "12px", borderRadius: "50%", backgroundColor: "#a78bfa", boxShadow: "0 0 10px #a78bfa" }} />
                      {rightTitle}
                    </div>
                    <p style={{ fontSize: "24px", color: "#e2e8f0", lineHeight: 1.6 }}>
                      {rightDesc}
                    </p>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* Visual Type 5: Bullet Points / Takeaways */}
        {scene.visual_type === "text_bullets" && (
          <div style={{ width: "100%", maxWidth: "1280px" }}>
            <h2
              style={{
                fontSize: "52px",
                fontWeight: 800,
                color: "#38bdf8",
                marginBottom: "40px",
                borderBottom: "2px solid rgba(56, 189, 248, 0.3)",
                paddingBottom: "20px",
              }}
            >
              {scene.text}
            </h2>
            <ul style={{ listStyleType: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "24px" }}>
              {Array.isArray(scene.visual_data.items) &&
                scene.visual_data.items.map((item: string, idx: number) => (
                  <li
                    key={idx}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      fontSize: "32px",
                      color: "#f1f5f9",
                      lineHeight: 1.5,
                      backgroundColor: "rgba(30, 41, 59, 0.5)",
                      padding: "20px 28px",
                      borderRadius: "16px",
                      border: "1px solid rgba(255, 255, 255, 0.06)",
                    }}
                  >
                    <span style={{ color: "#38bdf8", marginRight: "22px", fontSize: "30px" }}>✦</span>
                    <span>{item}</span>
                  </li>
                ))}
            </ul>
          </div>
        )}

        {/* Visual Type 6: Code Snippet (Dynamically auto-scaled to prevent any overflow) */}
        {scene.visual_type === "code_snippet" && (() => {
          const rawCode = scene.visual_data.code || scene.text || "";
          const codeLines = rawCode.split("\n");
          const lineCount = codeLines.length;

          let codeFontSize = "23px";
          let codeLineHeight = 1.45;
          let codePadding = "20px 28px";

          if (lineCount > 22) {
            codeFontSize = "15px";
            codeLineHeight = 1.25;
            codePadding = "12px 20px";
          } else if (lineCount > 17) {
            codeFontSize = "17px";
            codeLineHeight = 1.3;
            codePadding = "14px 22px";
          } else if (lineCount > 13) {
            codeFontSize = "19px";
            codeLineHeight = 1.35;
            codePadding = "16px 24px";
          } else if (lineCount > 9) {
            codeFontSize = "21px";
            codeLineHeight = 1.4;
            codePadding = "18px 26px";
          }

          const codeStr = rawCode.toLowerCase();
          const isSql = /select\b|create\s+table|insert\s+into|begin\s+transaction|commit|foreign\s+key|drop\s+table|references\b/.test(codeStr);
          const isCpp = /#include\b|std::|int\s+main\b|cout\b|nullptr|malloc\b|free\(/.test(codeStr);
          const filename = isSql ? "schema.sql" : isCpp ? "main.cpp" : "solution.py";
          const langTag = isSql ? "SQL (PostgreSQL)" : isCpp ? "C++20" : "Python 3";

          return (
            <div style={{ width: "100%", maxWidth: "1350px", maxHeight: "550px", display: "flex", flexDirection: "column" }}>
              <div
                style={{
                  backgroundColor: "#030712",
                  borderRadius: "20px",
                  border: "2px solid #334155",
                  overflow: "hidden",
                  boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.8)",
                  maxHeight: "540px",
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                {/* Window Title Bar */}
                <div
                  style={{
                    backgroundColor: "#0f172a",
                    padding: "12px 22px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    borderBottom: "1px solid #1e293b",
                    flexShrink: 0,
                  }}
                >
                  <div style={{ display: "flex", gap: "10px" }}>
                    <span style={{ width: "14px", height: "14px", borderRadius: "50%", backgroundColor: "#ef4444" }} />
                    <span style={{ width: "14px", height: "14px", borderRadius: "50%", backgroundColor: "#f59e0b" }} />
                    <span style={{ width: "14px", height: "14px", borderRadius: "50%", backgroundColor: "#10b981" }} />
                  </div>
                  <span style={{ fontSize: "18px", color: "#94a3b8", fontFamily: "monospace" }}>
                    {filename}
                  </span>
                  <span style={{ fontSize: "15px", color: "#38bdf8", fontWeight: 600 }}>{langTag}</span>
                </div>

                {/* Code Content */}
                <pre
                  style={{
                    padding: codePadding,
                    margin: 0,
                    fontSize: codeFontSize,
                    color: "#34d399",
                    fontFamily: "'Fira Code', 'Courier New', monospace",
                    lineHeight: codeLineHeight,
                    whiteSpace: "pre-wrap",
                    overflowY: "hidden",
                    maxHeight: "470px",
                  }}
                >
                  <code>{rawCode}</code>
                </pre>
              </div>
            </div>
          );
        })()}

        {/* Default / Fallback Concept Presentation with Smart Auto-Detection */}
        {[
          "title_card", "graph_chart", "array_memory", "tree_structure", "genai_transformer",
          "agentic_loop", "flow_steps", "comparison", "text_bullets", "code_snippet",
          "system_pipeline", "pipeline", "concept_network", "concept_map", "layer_stack",
          "stack_hierarchy", "cycle_loop", "circular_cycle", "comparison_matrix", "data_grid",
          "queue_structure", "queue_pipeline", "fifo_queue"
        ].indexOf(scene.visual_type) === -1 && (
          scene.visual_data?.stages ? (
            <SystemPipelineVisual visual_data={scene.visual_data} text={scene.text} />
          ) : scene.visual_data?.nodes ? (
            <ConceptNetworkVisual visual_data={scene.visual_data} text={scene.text} />
          ) : scene.visual_data?.layers ? (
            <LayerStackVisual visual_data={scene.visual_data} text={scene.text} />
          ) : scene.visual_data?.rows ? (
            <ComparisonMatrixVisual visual_data={scene.visual_data} text={scene.text} />
          ) : Array.isArray(scene.visual_data?.items) && scene.visual_data.items.length > 0 ? (
            <div style={{ width: "100%", maxWidth: "1280px" }}>
              <h2 style={{ fontSize: "52px", fontWeight: 800, color: "#38bdf8", marginBottom: "40px", borderBottom: "2px solid rgba(56, 189, 248, 0.3)", paddingBottom: "20px" }}>
                {scene.text}
              </h2>
              <ul style={{ listStyleType: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "24px" }}>
                {scene.visual_data.items.map((item: string, idx: number) => (
                  <li key={idx} style={{ display: "flex", alignItems: "flex-start", fontSize: "32px", color: "#f1f5f9", lineHeight: 1.5, backgroundColor: "rgba(30, 41, 59, 0.5)", padding: "20px 28px", borderRadius: "16px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                    <span style={{ color: "#38bdf8", marginRight: "22px", fontSize: "30px" }}>✦</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : Array.isArray(scene.visual_data?.steps) && scene.visual_data.steps.length > 0 ? (
            <div style={{ width: "100%", maxWidth: "1280px" }}>
              <h2 style={{ fontSize: "48px", fontWeight: 800, color: "#38bdf8", textAlign: "center", marginBottom: "40px" }}>
                {scene.text}
              </h2>
              <div style={{ display: "grid", gridTemplateColumns: `repeat(${Math.min(scene.visual_data.steps.length, 4)}, 1fr)`, gap: "24px" }}>
                {scene.visual_data.steps.map((step: any, idx: number) => (
                  <div key={idx} style={{ backgroundColor: "rgba(30, 41, 59, 0.7)", border: "2px solid rgba(56, 189, 248, 0.4)", borderRadius: "20px", padding: "32px 24px", display: "flex", flexDirection: "column" }}>
                    <div style={{ width: "52px", height: "52px", borderRadius: "14px", backgroundColor: "#38bdf8", color: "#0f172a", fontSize: "26px", fontWeight: 900, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "16px" }}>
                      {idx + 1}
                    </div>
                    <h3 style={{ fontSize: "26px", fontWeight: 700, color: "#f8fafc", marginBottom: "12px" }}>
                      {step.title || `Step ${idx + 1}`}
                    </h3>
                    <p style={{ fontSize: "20px", color: "#cbd5e1", lineHeight: 1.5 }}>
                      {step.desc || step.description || ""}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", maxWidth: "1280px" }}>
              <div
                style={{
                  display: "inline-block",
                  padding: "6px 20px",
                  borderRadius: "999px",
                  backgroundColor: "rgba(56, 189, 248, 0.15)",
                  border: "1px solid rgba(56, 189, 248, 0.35)",
                  color: "#38bdf8",
                  fontSize: "20px",
                  fontWeight: 700,
                  marginBottom: "20px",
                  letterSpacing: "1px",
                  textTransform: "uppercase",
                }}
              >
                ✦ Key Architectural Invariant
              </div>
              <h2 style={{ fontSize: "50px", fontWeight: 800, color: "#ffffff", marginBottom: "24px" }}>
                {scene.text}
              </h2>
              <div
                style={{
                  backgroundColor: "rgba(30, 41, 59, 0.75)",
                  border: "2px solid rgba(56, 189, 248, 0.3)",
                  borderRadius: "20px",
                  padding: "36px 44px",
                  boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5)",
                  maxWidth: "1100px",
                  margin: "0 auto",
                }}
              >
                <p style={{ fontSize: "28px", color: "#e2e8f0", lineHeight: 1.6, margin: 0 }}>
                  {scene.visual_data.description || scene.narration}
                </p>
              </div>
            </div>
          )
        )}
      </div>

      {/* Bottom Subtitle / Captions Dock Synchronized with Narration */}
      <div style={subtitleBarStyle}>
        <div
          style={{
            width: "42px",
            height: "42px",
            borderRadius: "50%",
            backgroundColor: "rgba(56, 189, 248, 0.25)",
            border: "1px solid rgba(56, 189, 248, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "22px",
            flexShrink: 0,
            boxShadow: "0 0 15px rgba(56, 189, 248, 0.3)",
          }}
        >
          🎙️
        </div>
        <p
          style={{
            margin: 0,
            fontSize: "26px",
            fontWeight: 600,
            color: "#ffffff",
            lineHeight: 1.35,
            textShadow: "0 2px 10px rgba(0, 0, 0, 0.95)",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            letterSpacing: "0.2px",
          }}
        >
          {scene.narration}
        </p>
      </div>
    </AbsoluteFill>
  );
};