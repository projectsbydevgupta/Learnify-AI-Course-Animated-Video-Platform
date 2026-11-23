"use client";

import { useState, useEffect, Suspense } from "react";
import { useUser } from "@clerk/nextjs";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { VideoGenerationProgress } from "../../../components/VideoGenerationProgress";

function GenerateTopicForm() {
  const { user } = useUser();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [targetTopicId, setTargetTopicId] = useState("");

  useEffect(() => {
    const urlTopic = searchParams.get("topic");
    if (urlTopic) setTopic(urlTopic);
  }, [searchParams]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || !user) return;

    setLoading(true);
    setStatusText("Initializing autonomous background pipeline...");

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      // Clean deterministic ID without difficulty labels
      const cleanSlug = topic.toLowerCase().replace(/[^a-z0-9]+/g, '_').slice(0, 32);
      const formattedId = `${cleanSlug}_${Date.now().toString(36).slice(-6)}`;
      
      setTargetTopicId(formattedId); 
      console.log(`[PIPELINE] Launching topic generation: id=${formattedId}, title=${topic.trim()}`);
      
      const res = await fetch(`${backendUrl}/api/jobs/generate-video`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic_id: formattedId,
          title: topic.trim(),
          difficulty: "Advanced", // Preserves the comprehensive ~2 minute, 8-scene depth under the hood
          content: `Comprehensive explanation and architecture of ${topic} tailored to its domain depth.`
        })
      });

      if (!res.ok) throw new Error("Failed to start job");

      const data = await res.json();
      setJobId(data.job_id);

    } catch (err) {
      console.error(err);
      setStatusText("Failed to initialize topic generation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl w-full bg-slate-900/80 border border-slate-800/90 p-8 sm:p-10 rounded-3xl shadow-2xl backdrop-blur-2xl relative overflow-hidden">
      <div className="absolute -top-24 -right-24 w-60 h-60 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="mb-8">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-semibold mb-4 transition group"
        >
          <span className="group-hover:-translate-x-1 transition-transform">←</span> Back to Studio Dashboard
        </Link>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-xl shadow-inner">
            ⚡
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Generate Topic Course & Video
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              1080p Animated Video • RAG Verification • Interactive Quiz
            </p>
          </div>
        </div>
      </div>

      {!jobId ? (
        <form onSubmit={handleGenerate} className="space-y-6">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Topic or Concept Title
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Binary Search, TCP/IP Model, Transformer Attention, Gradient Descent"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full px-4 py-3.5 bg-slate-950/90 border border-slate-700/80 rounded-xl focus:outline-none focus:border-cyan-500 text-slate-100 placeholder-slate-500 text-sm shadow-inner transition"
            />
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-400 space-y-1.5">
            <div className="flex items-center gap-2 text-cyan-300 font-semibold">
              <span>🛡️</span> Autonomous Topic Pipeline:
            </div>
            <p className="leading-relaxed">
              Generates a comprehensive animated video (~2 mins, 8 scenes), structured educational explanation, fact-verified claims, and an interactive quiz tailored directly to the topic depth.
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || !topic.trim()}
            className="w-full py-4 text-white rounded-xl font-bold shadow-lg transition cursor-pointer text-sm disabled:opacity-50 bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 shadow-purple-950/50"
          >
            {loading ? "Starting Background Worker..." : "🚀 Generate Topic Video & Course"}
          </button>

          {loading && (
            <p className="text-xs text-center text-cyan-400 animate-pulse">{statusText}</p>
          )}
        </form>
      ) : (
        <div className="w-full space-y-6">
          <VideoGenerationProgress 
            jobId={jobId} 
            onComplete={() => router.push(`/topics/${targetTopicId}`)} 
          />
          <button
            onClick={() => {
              setJobId(null);
              setTopic("");
            }}
            className="w-full py-3 bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition cursor-pointer"
          >
            ← Generate another topic
          </button>
        </div>
      )}
    </div>
  );
}

export default function GenerateTopicPage() {
  return (
    <main className="min-h-screen bg-[#070b14] text-slate-100 flex items-center justify-center p-6 selection:bg-cyan-500 selection:text-black">
      <Suspense fallback={<div className="text-slate-400 animate-pulse">Loading generator...</div>}>
        <GenerateTopicForm />
      </Suspense>
    </main>
  );
}