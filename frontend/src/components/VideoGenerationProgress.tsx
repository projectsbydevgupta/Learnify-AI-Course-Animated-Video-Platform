"use client";

import React, { useState, useEffect } from "react";

interface StepState {
  research: "pending" | "in_progress" | "completed";
  content: "pending" | "in_progress" | "completed";
  verification?: "pending" | "in_progress" | "completed";
  script: "pending" | "in_progress" | "completed";
  visuals: "pending" | "in_progress" | "completed";
  tts: "pending" | "in_progress" | "completed";
  rendering: "pending" | "in_progress" | "completed";
}

interface JobStatusResponse {
  job_id: string;
  progress: number;
  status: string;
  steps: StepState;
  video_url?: string | null;
  error?: string | null;
}

export const VideoGenerationProgress: React.FC<{ jobId: string; onComplete?: () => void }> = ({ jobId, onComplete }) => {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    if (!jobId) return;
    let isDone = false;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${backendUrl}/api/jobs/${jobId}/status`);
        const data: JobStatusResponse = await res.json();
        setJob(data);

        // Stop polling if the job is done or failed
        if (data.status === "COMPLETED" || data.status === "FAILED") {
          clearInterval(interval);
          
          // Wait 2 seconds so the user sees the "Complete!" message, then trigger redirect
          if (data.status === "COMPLETED" && onComplete && !isDone) {
            isDone = true;
            setTimeout(() => onComplete(), 2000);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2000); // Polls every 2 seconds

    return () => clearInterval(interval);
  }, [jobId, onComplete]);

  if (!job) return <div className="text-gray-400">Initializing background job...</div>;

  const stepOrder: (keyof StepState)[] = [
    "research",
    "content",
    "verification",
    "script",
    "visuals",
    "tts",
    "rendering"
  ];

  const resolveStepStatus = (stepKey: keyof StepState): "pending" | "in_progress" | "completed" => {
    if (job.status === "COMPLETED") return "completed";
    // Guard: if steps is missing/undefined (e.g. DB fallback response), treat everything as pending
    const steps = job.steps;
    if (!steps) return "pending";
    const raw = steps[stepKey];
    if (raw === "completed") return "completed";

    // If any later step is in_progress or completed, this step is definitely completed
    const currentIndex = stepOrder.indexOf(stepKey);
    const anyLaterActive = stepOrder.slice(currentIndex + 1).some(
      (k) => steps[k] === "in_progress" || steps[k] === "completed"
    );
    if (anyLaterActive) return "completed";

    return raw || "pending";
  };

  const renderStepStatus = (label: string, stepKey: keyof StepState) => {
    const state = resolveStepStatus(stepKey);
    return (
      <div className="flex justify-between items-center py-2 border-b border-gray-800 text-sm">
        <span className="text-gray-300 font-medium">{label}</span>
        <span>
          {state === "completed" && <span className="text-green-400 font-bold">✓ Done</span>}
          {state === "in_progress" && <span className="text-amber-400 animate-pulse">... Generating</span>}
          {state === "pending" && <span className="text-gray-600">Pending</span>}
        </span>
      </div>
    );
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white max-w-lg shadow-xl w-full">
      <h3 className="text-xl font-bold mb-2">Generating Lesson Video</h3>
      <p className="text-xs text-gray-400 mb-4">Job ID: {job.job_id}</p>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 rounded-full h-3 mb-6 overflow-hidden">
        <div
          className="bg-indigo-500 h-full transition-all duration-500 ease-out"
          style={{ width: `${job.progress}%` }}
        />
      </div>

      {/* Step Checklist */}
      <div className="space-y-1 mb-6">
        {renderStepStatus("Curriculum Research", "research")}
        {renderStepStatus("Lesson Content Drafting", "content")}
        {job.steps?.verification && renderStepStatus("LLM-as-a-Judge Audit (Gemini)", "verification")}
        {renderStepStatus("Script Planning", "script")}
        {renderStepStatus("Visual Scene Design", "visuals")}
        {renderStepStatus("TTS Voiceover Sync", "tts")}
        {renderStepStatus("Remotion Video Render", "rendering")}
      </div>

      {/* Output Video Player */}
      {job.status === "COMPLETED" && job.video_url && (
        <div className="mt-4">
          <p className="text-green-400 text-sm font-semibold mb-2">🎉 Video Generation Complete!</p>
          <video
            controls
            src={`${backendUrl}${job.video_url}`}
            className="w-full rounded-lg border border-slate-700 shadow-md"
          />
        </div>
      )}

      {job.status === "FAILED" && (
        <div className="text-red-400 text-sm font-semibold mt-2">
          ❌ Generation Failed: {job.error}
        </div>
      )}
    </div>
  );
};